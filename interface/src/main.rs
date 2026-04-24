//! Two agents (Desktop and Pi) debate a topic using your local model servers.
//!
//! Desktop runs vLLM, Pi runs llama-cpp — both expose an OpenAI-compatible API.
//! Start them first:
//!   desktop:  vllm serve $DESKTOP_MODEL --port 8000
//!   pi:       python -m llama_cpp.server --model $PI_MODEL_PATH --host 0.0.0.0 --port 8000
//!
//! cargo run --manifest-path interface/Cargo.toml -- "your topic"
//!
//! Ctrl+P or Enter to cut in with your own message. Ctrl+Q to quit.

use anyhow::Result;
use crossterm::{
    event::{self, Event, KeyCode, KeyModifiers},
    terminal,
};
use rig::providers::openai;
use rig::completion::Prompt;
use std::{
    env,
    fs,
    io::{self, Write},
    sync::mpsc,
    time::Duration,
};
use tokio::time::sleep;

const MAX_HISTORY_TURNS: usize = 8;
const TURN_DELAY_MS: u64 = 300;

const RESET:  &str = "\x1b[0m";
const BOLD:   &str = "\x1b[1m";
const DIM:    &str = "\x1b[2m";
const CYAN:   &str = "\x1b[96m";
const YELLOW: &str = "\x1b[93m";
const GREEN:  &str = "\x1b[92m";

enum UiEvent {
    Quit,
    Inject(String),
}

struct History(Vec<String>);

impl History {
    fn new() → Self { Self(Vec::new()) }

    fn push(&mut self, role: &str, text: &str) {
        self.0.push(format!("[{role}]: {text}"));
        if self.0.len() > MAX_HISTORY_TURNS {
            self.0.remove(0);
        }
    }

    fn prompt_for(&self, topic: &str, speaker: &str) → String {
        let mut s = format!("Topic: {topic}\n\nConversation so far:\n");
        for line in &self.0 {
            s.push_str(line);
            s.push('\n');
        }
        s.push_str(&format!(
            "\nYou are {speaker}. Continue with your next reply only. \
             Do not repeat the topic or label your response."
        ));
        s
    }
}

// Runs in its own thread; puts terminal in raw mode so we can catch Ctrl chords.
// Switches back to normal mode when it needs to read a line from the user.
fn spawn_keyboard_thread(tx: mpsc::SyncSender<UiEvent>) {
    std::thread::spawn(move || {
        if terminal::enable_raw_mode().is_err() {
            return;
        }

        loop {
            if event::poll(Duration::from_millis(100)).unwrap_or(false) {
                let Ok(Event::Key(key)) = event::read() else { continue };

                let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);

                if ctrl && key.code == KeyCode::Char('q') {
                    terminal::disable_raw_mode().ok();
                    tx.send(UiEvent::Quit).ok();
                    break;
                }

                let wants_to_inject = (ctrl && key.code == KeyCode::Char('p'))
                    || key.code == KeyCode::Enter;

                if wants_to_inject {
                    terminal::disable_raw_mode().ok();
                    print!("\n{GREEN}{BOLD}[You]: {RESET}");
                    io::stdout().flush().ok();

                    let mut line = String::new();
                    io::stdin().read_line(&mut line).ok();
                    let msg = line.trim().to_string();

                    terminal::enable_raw_mode().ok();

                    if !msg.is_empty() {
                        if tx.send(UiEvent::Inject(msg)).is_err() {
                            break;
                        }
                    }
                }
            }
        }
    });
}

/// Read interface/.ports written by router.py, returns (desktop_url, pi_url).
fn read_ports_file() → Option<(String, String)> {
    let content = fs::read_to_string("interface/.ports").ok()?;
    let mut desktop = None;
    let mut pi = None;
    for line in content.lines() {
        if let Some(v) = line.strip_prefix("desktop=") { desktop = Some(v.to_string()); }
        if let Some(v) = line.strip_prefix("pi=")      { pi      = Some(v.to_string()); }
    }
    Some((desktop?, pi?))
}

#[tokio::main]
async fn main() → Result<()> {
    dotenvy::dotenv().ok();

    // Auto-discover ports from router.py, env vars override if set.
    let (auto_desktop, auto_pi) = read_ports_file()
        .unwrap_or_else(|| (
            "http://localhost:8100/v1".to_string(),
            "http://localhost:8101/v1".to_string(),
        ));

    let desktop_endpoint = env::var("DESKTOP_ENDPOINT").unwrap_or(auto_desktop);
    let desktop_model    = env::var("DESKTOP_MODEL")
        .unwrap_or_else(|_| "Qwen/Qwen2.5-7B-Instruct-AWQ".to_string());
    let pi_endpoint = env::var("PI_ENDPOINT").unwrap_or(auto_pi);
    let pi_model    = env::var("PI_MODEL_NAME")
        .unwrap_or_else(|_| "tinyllama".to_string());

    let topic: String = env::args().nth(1).unwrap_or_else(|| {
        print!("{BOLD}Topic:{RESET} ");
        io::stdout().flush().unwrap();
        let mut s = String::new();
        io::stdin().read_line(&mut s).unwrap();
        let t = s.trim().to_string();
        if t.is_empty() { "whether small things can have big impact".to_string() } else { t }
    });

    // Both clients point at local servers — no cloud API involved.
    let desktop_client = openai::Client::from_url("not-needed", &desktop_endpoint);
    let pi_client      = openai::Client::from_url("not-needed", &pi_endpoint);

    let desktop = desktop_client
        .agent(&desktop_model)
        .preamble(&format!(
            "You are Desktop, a large GPU-accelerated model on a powerful PC. \
             You are verbose, analytical, and expansive. \
             You are debating: '{topic}'. Reply in 3-4 sentences. \
             Address the other speaker directly."
        ))
        .build();

    let pi = pi_client
        .agent(&pi_model)
        .preamble(&format!(
            "You are Pi, a small efficient model on a Raspberry Pi. \
             You are concise and direct. \
             You are debating: '{topic}'. Reply in 1-2 sentences max."
        ))
        .build();

    let (tx, rx) = mpsc::sync_channel::<UiEvent>(16);
    spawn_keyboard_thread(tx);

    println!("\n{DIM}{}{RESET}", "─".repeat(60));
    println!("{BOLD}Topic:{RESET} {topic}");
    println!("{DIM}Desktop → {desktop_endpoint}  |  Pi → {pi_endpoint}{RESET}");
    println!("{DIM}Ctrl+P or Enter to interject  |  Ctrl+Q to quit{RESET}");
    println!("{DIM}{}{RESET}\n", "─".repeat(60));

    let mut history = History::new();
    let mut turn = 0usize;

    // Desktop goes first, then Pi, alternating. last_reply feeds the next prompt.
    let mut last_reply = format!("Let's discuss: {topic}");

    loop {
        // Pick up any key events that came in during the last generation.
        loop {
            match rx.try_recv() {
                Ok(UiEvent::Quit) => {
                    terminal::disable_raw_mode().ok();
                    println!("\n{DIM}Bye.{RESET}");
                    return Ok(());
                }
                Ok(UiEvent::Inject(msg)) => {
                    println!("{GREEN}{BOLD}[You]{RESET}  {msg}");
                    history.push("You (observer)", &msg);
                    last_reply = format!("{last_reply}\n[You (observer)]: {msg}");
                }
                Err(_) => break,
            }
        }

        let is_desktop = turn % 2 == 0;
        let (agent, name, color) = if is_desktop {
            (&desktop, "Desktop", CYAN)
        } else {
            (&pi, "Pi", YELLOW)
        };

        let prompt = if turn == 0 {
            format!("Please open the discussion on: '{topic}'")
        } else {
            history.prompt_for(&topic, name)
        };

        print!("\n{color}{BOLD}[{name}]{RESET}  ");
        io::stdout().flush()?;

        let reply = match agent.prompt(prompt.as_str()).await {
            Ok(r) => r,
            Err(e) => {
                eprintln!("\n{BOLD}Error:{RESET} {e}");
                break;
            }
        };

        let reply = reply.trim().to_string();
        println!("{reply}");

        history.push(name, &reply);
        last_reply = reply;
        turn += 1;

        sleep(Duration::from_millis(TURN_DELAY_MS)).await;
    }

    terminal::disable_raw_mode().ok();
    println!("\n{DIM}{}{RESET}", "─".repeat(60));
    Ok(())
}
