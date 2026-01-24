#!/usr/bin/env node
/**
 * stts.mjs - Universal STT/TTS Shell Wrapper (Node.js ESM)
 * Cross-platform voice shell with automatic model download and hardware detection.
 *
 * Usage:
 *   ./stts.mjs                  # Interactive voice shell
 *   ./stts.mjs --setup          # Configure STT/TTS providers
 *   ./stts.mjs [cmd] [args]     # Run command with voice output
 */

import { spawn, execSync, spawnSync } from 'node:child_process';
import { platform, homedir, cpus, totalmem, arch } from 'node:os';
import { readFileSync, writeFileSync, existsSync, mkdirSync, unlinkSync, chmodSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { get as httpsGet } from 'node:https';
import { createWriteStream } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

let __version__ = '0.0.0';
try {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = dirname(__filename);
    __version__ = readFileSync(join(__dirname, 'VERSION'), 'utf8').trim();
} catch {}

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG_DIR = join(homedir(), '.config', 'stts');
const CONFIG_FILE = join(CONFIG_DIR, 'config.json');
const MODELS_DIR = join(CONFIG_DIR, 'models');
const HISTORY_FILE = join(CONFIG_DIR, 'history');

const DEFAULT_CONFIG = {
    stt_provider: null,
    tts_provider: null,
    stt_model: null,
    tts_voice: 'pl',
    language: 'pl',
    timeout: 5,
    auto_tts: true,
};

// ═══════════════════════════════════════════════════════════════════════════════
// COLORS
// ═══════════════════════════════════════════════════════════════════════════════

const Colors = {
    RED: '\x1b[0;31m',
    GREEN: '\x1b[0;32m',
    YELLOW: '\x1b[0;33m',
    BLUE: '\x1b[0;34m',
    MAGENTA: '\x1b[0;35m',
    CYAN: '\x1b[0;36m',
    BOLD: '\x1b[1m',
    NC: '\x1b[0m',
};

function cprint(color, text, newline = true) {
    process.stdout.write(`${color}${text}${Colors.NC}${newline ? '\n' : ''}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SYSTEM DETECTION
// ═══════════════════════════════════════════════════════════════════════════════

function detectSystem() {
    const osName = platform();
    const archName = arch();
    const cpuCores = cpus().length;
    const ramGb = Math.round(totalmem() / 1024 / 1024 / 1024 * 10) / 10;

    // GPU detection
    let gpuName = null;
    let gpuVramGb = null;
    try {
        const result = execSync(
            'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits',
            { encoding: 'utf8', timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'] }
        );
        const parts = result.trim().split(', ');
        gpuName = parts[0];
        gpuVramGb = parts[1] ? Math.round(parseFloat(parts[1]) / 1024 * 10) / 10 : null;
    } catch {}

    // RPi detection
    let isRpi = false;
    try {
        if (osName === 'linux' && existsSync('/proc/device-tree/model')) {
            const model = readFileSync('/proc/device-tree/model', 'utf8');
            isRpi = model.toLowerCase().includes('raspberry');
        }
    } catch {}

    // Microphone detection
    let hasMic = false;
    try {
        if (osName === 'linux') {
            const result = execSync('arecord -l', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
            hasMic = result.toLowerCase().includes('card');
        } else {
            hasMic = true; // macOS/Windows usually have mic
        }
    } catch {}

    return {
        osName,
        osVersion: process.release?.name || 'unknown',
        arch: archName,
        cpuCores,
        ramGb,
        gpuName,
        gpuVramGb,
        isRpi,
        hasMic,
    };
}

function printSystemInfo(info) {
    cprint(Colors.CYAN, '\n═══ SYSTEM INFO ═══');
    console.log(`  OS:        ${info.osName}`);
    console.log(`  Arch:      ${info.arch}`);
    console.log(`  CPU:       ${info.cpuCores} cores`);
    console.log(`  RAM:       ${info.ramGb} GB`);
    if (info.gpuName) {
        console.log(`  GPU:       ${info.gpuName} (${info.gpuVramGb} GB VRAM)`);
    } else {
        console.log(`  GPU:       None detected (CPU only)`);
    }
    console.log(`  RPi:       ${info.isRpi ? 'Yes' : 'No'}`);
    console.log(`  Mic:       ${info.hasMic ? 'Yes' : 'No (install alsa-utils)'}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function which(cmd) {
    try {
        const result = execSync(`which ${cmd}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
        return result.trim();
    } catch {
        return null;
    }
}

function ensureDir(dir) {
    if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
    }
}

function downloadFile(url, destPath) {
    return new Promise((resolve, reject) => {
        ensureDir(dirname(destPath));
        const file = createWriteStream(destPath);
        
        const request = (url) => {
            httpsGet(url, (response) => {
                if (response.statusCode === 302 || response.statusCode === 301) {
                    request(response.headers.location);
                    return;
                }
                
                const totalSize = parseInt(response.headers['content-length'], 10);
                let downloaded = 0;
                
                response.on('data', (chunk) => {
                    downloaded += chunk.length;
                    const percent = totalSize ? Math.round(downloaded / totalSize * 100) : 0;
                    process.stdout.write(`\r  Progress: ${percent}%`);
                });
                
                response.pipe(file);
                file.on('finish', () => {
                    file.close();
                    console.log();
                    resolve(destPath);
                });
            }).on('error', (err) => {
                unlinkSync(destPath);
                reject(err);
            });
        };
        
        request(url);
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
// STT PROVIDERS
// ═══════════════════════════════════════════════════════════════════════════════

const STT_PROVIDERS = {
    whisper_cpp: {
        name: 'whisper.cpp',
        description: 'Offline, fast, CPU-optimized Whisper (recommended)',
        minRamGb: 1.0,
        models: [
            ['tiny', 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin', 0.08],
            ['base', 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin', 0.15],
            ['small', 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin', 0.5],
            ['medium', 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin', 1.5],
            ['large', 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin', 3.0],
        ],
        isAvailable: () => {
            if (which('whisper-cpp') || which('main')) return [true, 'whisper.cpp found'];
            const whisperBin = join(MODELS_DIR, 'whisper.cpp', 'main');
            if (existsSync(whisperBin)) return [true, `whisper.cpp at ${whisperBin}`];
            return [false, 'whisper.cpp not installed'];
        },
        getRecommendedModel: (info) => {
            if (info.ramGb < 2) return 'tiny';
            if (info.ramGb < 4) return 'base';
            if (info.ramGb < 8) return 'small';
            if (info.ramGb < 16) return 'medium';
            return 'large';
        },
        install: async () => {
            cprint(Colors.YELLOW, '📦 Installing whisper.cpp...');
            const whisperDir = join(MODELS_DIR, 'whisper.cpp');
            ensureDir(whisperDir);
            
            try {
                if (!existsSync(join(whisperDir, 'Makefile'))) {
                    execSync(`git clone https://github.com/ggerganov/whisper.cpp "${whisperDir}"`, { stdio: 'inherit' });
                }
                execSync('make -j', { cwd: whisperDir, stdio: 'inherit' });
                cprint(Colors.GREEN, '✅ whisper.cpp installed!');
                return true;
            } catch (e) {
                cprint(Colors.RED, `❌ Installation failed: ${e.message}`);
                return false;
            }
        },
        downloadModel: async (modelName) => {
            const modelInfo = STT_PROVIDERS.whisper_cpp.models.find(m => m[0] === modelName);
            if (!modelInfo) {
                cprint(Colors.RED, `❌ Unknown model: ${modelName}`);
                return null;
            }
            
            const [name, url, size] = modelInfo;
            const modelPath = join(MODELS_DIR, 'whisper.cpp', `ggml-${name}.bin`);
            
            if (existsSync(modelPath)) {
                cprint(Colors.GREEN, `✅ Model ${name} already downloaded`);
                return modelPath;
            }
            
            cprint(Colors.YELLOW, `📥 Downloading ${name} model (${size} GB)...`);
            try {
                await downloadFile(url, modelPath);
                cprint(Colors.GREEN, `✅ Model ${name} downloaded!`);
                return modelPath;
            } catch (e) {
                cprint(Colors.RED, `❌ Download failed: ${e.message}`);
                return null;
            }
        },
        transcribe: async (audioPath, model, language) => {
            let whisperBin = which('whisper-cpp') || which('main');
            if (!whisperBin) {
                whisperBin = join(MODELS_DIR, 'whisper.cpp', 'main');
            }
            
            const modelPath = join(MODELS_DIR, 'whisper.cpp', `ggml-${model || 'base'}.bin`);
            if (!existsSync(modelPath)) {
                await STT_PROVIDERS.whisper_cpp.downloadModel(model || 'base');
            }
            
            try {
                const result = execSync(
                    `"${whisperBin}" -m "${modelPath}" -l ${language} -f "${audioPath}" -nt`,
                    { encoding: 'utf8', timeout: 60000, stdio: ['pipe', 'pipe', 'pipe'] }
                );
                return result.trim();
            } catch (e) {
                cprint(Colors.RED, `❌ Transcription error: ${e.message}`);
                return '';
            }
        },
    },
    
    google: {
        name: 'google',
        description: 'Google Speech API (online, requires sox)',
        minRamGb: 0.5,
        models: [],
        isAvailable: () => {
            if (which('sox')) return [true, 'sox found (for audio conversion)'];
            return [false, 'apt install sox'];
        },
        getRecommendedModel: () => null,
        install: async () => {
            cprint(Colors.YELLOW, '📦 sox is needed for audio conversion');
            cprint(Colors.YELLOW, 'Run: sudo apt install sox');
            return false;
        },
        transcribe: async (audioPath, model, language) => {
            cprint(Colors.YELLOW, '⚠️  Google STT requires API setup - use whisper.cpp instead');
            return '';
        },
    },
};

// ═══════════════════════════════════════════════════════════════════════════════
// TTS PROVIDERS
// ═══════════════════════════════════════════════════════════════════════════════

const TTS_PROVIDERS = {
    espeak: {
        name: 'espeak',
        description: 'Basic offline TTS (fast, low quality)',
        minRamGb: 0.1,
        isAvailable: () => {
            if (which('espeak') || which('espeak-ng')) return [true, 'espeak found'];
            return [false, 'apt install espeak'];
        },
        install: async (info) => {
            if (info.osName === 'linux') {
                cprint(Colors.YELLOW, '📦 Installing espeak...');
                try {
                    execSync('sudo apt install -y espeak', { stdio: 'inherit' });
                    return true;
                } catch {}
            }
            cprint(Colors.RED, '❌ Install manually: sudo apt install espeak');
            return false;
        },
        speak: (text, voice) => {
            const cmd = which('espeak-ng') || which('espeak');
            if (cmd) {
                try {
                    spawnSync(cmd, ['-v', voice, '-s', '160', text], { stdio: 'ignore' });
                } catch {}
            }
        },
    },
    
    piper: {
        name: 'piper',
        description: 'High-quality offline TTS (neural, recommended)',
        minRamGb: 0.5,
        voices: [
            ['pl_PL-gosia-medium', 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx'],
            ['en_US-lessac-medium', 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx'],
        ],
        isAvailable: () => {
            if (which('piper')) return [true, 'piper found'];
            const piperBin = join(MODELS_DIR, 'piper', 'piper', 'piper');
            if (existsSync(piperBin)) return [true, `piper at ${piperBin}`];
            return [false, 'piper not installed'];
        },
        install: async (info) => {
            cprint(Colors.YELLOW, '📦 Installing piper...');
            const piperDir = join(MODELS_DIR, 'piper');
            ensureDir(piperDir);
            
            let url;
            if (info.osName === 'linux') {
                if (info.arch === 'x64' || info.arch === 'x86_64') {
                    url = 'https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz';
                } else if (info.arch === 'arm64' || info.arch === 'aarch64') {
                    url = 'https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz';
                } else {
                    cprint(Colors.RED, `❌ Unsupported arch: ${info.arch}`);
                    return false;
                }
            } else if (info.osName === 'darwin') {
                url = 'https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_macos_x64.tar.gz';
            } else {
                cprint(Colors.RED, '❌ Piper not available for Windows, use espeak');
                return false;
            }
            
            try {
                const tarPath = join(piperDir, 'piper.tar.gz');
                cprint(Colors.YELLOW, '📥 Downloading piper...');
                await downloadFile(url, tarPath);
                
                execSync(`tar -xzf "${tarPath}" -C "${piperDir}"`, { stdio: 'inherit' });
                unlinkSync(tarPath);
                
                const piperBin = join(piperDir, 'piper', 'piper');
                if (existsSync(piperBin)) {
                    chmodSync(piperBin, 0o755);
                }
                
                cprint(Colors.GREEN, '✅ piper installed!');
                return true;
            } catch (e) {
                cprint(Colors.RED, `❌ Installation failed: ${e.message}`);
                return false;
            }
        },
        downloadVoice: async (voiceName) => {
            let voiceInfo = TTS_PROVIDERS.piper.voices.find(v => v[0] === voiceName);
            if (!voiceInfo) voiceInfo = TTS_PROVIDERS.piper.voices[0];
            
            const [name, url] = voiceInfo;
            const voicePath = join(MODELS_DIR, 'piper', 'voices', `${name}.onnx`);
            const jsonPath = voicePath + '.json';
            
            if (existsSync(voicePath)) return voicePath;
            
            cprint(Colors.YELLOW, `📥 Downloading voice ${name}...`);
            ensureDir(dirname(voicePath));
            
            try {
                await downloadFile(url, voicePath);
                await downloadFile(url + '.json', jsonPath);
                cprint(Colors.GREEN, `✅ Voice ${name} downloaded!`);
                return voicePath;
            } catch (e) {
                cprint(Colors.RED, `❌ Download failed: ${e.message}`);
                return null;
            }
        },
        speak: async (text, voice) => {
            let piperBin = which('piper');
            if (!piperBin) {
                piperBin = join(MODELS_DIR, 'piper', 'piper', 'piper');
            }
            
            const voiceName = voice === 'pl' ? 'pl_PL-gosia-medium' : 'en_US-lessac-medium';
            const voicePath = await TTS_PROVIDERS.piper.downloadVoice(voiceName);
            
            if (!voicePath) {
                TTS_PROVIDERS.espeak.speak(text, voice);
                return;
            }
            
            try {
                const piper = spawn(piperBin, ['--model', voicePath, '--output-raw'], { stdio: ['pipe', 'pipe', 'ignore'] });
                const aplay = spawn('aplay', ['-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-'], { stdio: ['pipe', 'ignore', 'ignore'] });
                
                piper.stdout.pipe(aplay.stdin);
                piper.stdin.write(text);
                piper.stdin.end();
                
                await new Promise(resolve => aplay.on('close', resolve));
            } catch (e) {
                cprint(Colors.RED, `❌ TTS error: ${e.message}`);
                TTS_PROVIDERS.espeak.speak(text, voice);
            }
        },
    },
    
    system: {
        name: 'system',
        description: 'System TTS (macOS say, Windows SAPI)',
        minRamGb: 0.1,
        isAvailable: (info) => {
            if (info?.osName === 'darwin') return [true, 'macOS say'];
            if (info?.osName === 'win32') return [true, 'Windows SAPI'];
            return [false, 'Linux: use espeak or piper'];
        },
        install: async () => false,
        speak: (text, voice) => {
            const os = platform();
            if (os === 'darwin') {
                spawnSync('say', ['-v', voice === 'pl' ? 'Zosia' : 'Samantha', text], { stdio: 'ignore' });
            } else if (os === 'win32') {
                const psCmd = `Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("${text.replace(/"/g, '""')}")`;
                spawnSync('powershell', ['-c', psCmd], { stdio: 'ignore' });
            }
        },
    },
};

// ═══════════════════════════════════════════════════════════════════════════════
// AUDIO RECORDING
// ═══════════════════════════════════════════════════════════════════════════════

function recordAudio(duration = 5, outputPath = '/tmp/stts_audio.wav') {
    const info = detectSystem();
    
    cprint(Colors.GREEN, `🎤 Mów (${duration}s)... `, false);
    
    try {
        if (info.osName === 'linux') {
            execSync(`arecord -d ${duration} -f cd -t wav "${outputPath}"`, { stdio: 'ignore', timeout: (duration + 2) * 1000 });
        } else if (info.osName === 'darwin') {
            execSync(`rec -r 16000 -c 1 "${outputPath}" trim 0 ${duration}`, { stdio: 'ignore', timeout: (duration + 2) * 1000 });
        } else {
            cprint(Colors.RED, '❌ Windows: use Python version');
            return '';
        }
        console.log('✅');
        return outputPath;
    } catch (e) {
        cprint(Colors.RED, `❌ Recording failed: ${e.message}`);
        return '';
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

function loadConfig() {
    ensureDir(CONFIG_DIR);
    if (existsSync(CONFIG_FILE)) {
        try {
            return JSON.parse(readFileSync(CONFIG_FILE, 'utf8'));
        } catch {}
    }
    return { ...DEFAULT_CONFIG };
}

function saveConfig(config) {
    ensureDir(CONFIG_DIR);
    writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

// ═══════════════════════════════════════════════════════════════════════════════
// INTERACTIVE SETUP
// ═══════════════════════════════════════════════════════════════════════════════

async function question(rl, prompt) {
    return new Promise(resolve => rl.question(prompt, resolve));
}

async function interactiveSetup() {
    const config = loadConfig();
    const info = detectSystem();
    
    cprint(Colors.BOLD + Colors.CYAN, `
╔═══════════════════════════════════════════════════════════════════╗
║                    🎙️  STTS - Setup Wizard (Node.js)              ║
╚═══════════════════════════════════════════════════════════════════╝
`);
    
    printSystemInfo(info);
    
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    
    // STT Selection
    cprint(Colors.CYAN, '\n═══ STT (Speech-to-Text) ═══');
    console.log('\nDostępne providery:');
    
    const sttOptions = Object.entries(STT_PROVIDERS);
    for (let i = 0; i < sttOptions.length; i++) {
        const [name, provider] = sttOptions[i];
        const [available, reason] = provider.isAvailable();
        const status = available ? `${Colors.GREEN}✅` : `${Colors.YELLOW}⚠️`;
        const recModel = provider.getRecommendedModel?.(info);
        const canRun = info.ramGb >= provider.minRamGb;
        const runStatus = canRun ? `${Colors.GREEN}(OK)` : `${Colors.RED}(za słaby sprzęt)`;
        
        console.log(`  ${status} ${i + 1}. ${provider.name}${Colors.NC} - ${provider.description}`);
        console.log(`      Wymagania: RAM≥${provider.minRamGb}GB ${runStatus}${Colors.NC}`);
        console.log(`      Status: ${reason}`);
        if (recModel) console.log(`      Rekomendowany model: ${recModel}`);
    }
    
    console.log();
    while (true) {
        const choice = await question(rl, `Wybierz STT (1-${sttOptions.length}, ENTER=skip): `);
        if (!choice) break;
        
        const idx = parseInt(choice) - 1;
        if (idx >= 0 && idx < sttOptions.length) {
            const [name, provider] = sttOptions[idx];
            const [available] = provider.isAvailable();
            
            if (!available) {
                const install = await question(rl, `📦 ${provider.name} nie jest zainstalowany. Zainstalować? (y/n): `);
                if (install.toLowerCase() === 'y') {
                    await provider.install(info);
                }
            }
            
            config.stt_provider = name;
            
            if (provider.models?.length) {
                const recModel = provider.getRecommendedModel(info);
                console.log(`\nDostępne modele (rekomendowany: ${recModel}):`);
                for (let j = 0; j < provider.models.length; j++) {
                    const [mname, , msize] = provider.models[j];
                    const recMark = mname === recModel ? ' ← rekomendowany' : '';
                    console.log(`  ${j + 1}. ${mname} (${msize} GB)${recMark}`);
                }
                
                const modelChoice = await question(rl, `Wybierz model (1-${provider.models.length}, ENTER=${recModel}): `);
                if (modelChoice) {
                    const midx = parseInt(modelChoice) - 1;
                    if (midx >= 0 && midx < provider.models.length) {
                        config.stt_model = provider.models[midx][0];
                    } else {
                        config.stt_model = recModel;
                    }
                } else {
                    config.stt_model = recModel;
                }
                
                const download = await question(rl, `📥 Pobrać model ${config.stt_model} teraz? (y/n): `);
                if (download.toLowerCase() === 'y' && provider.downloadModel) {
                    await provider.downloadModel(config.stt_model);
                }
            }
            break;
        }
        cprint(Colors.RED, '❌ Nieprawidłowy wybór');
    }
    
    // TTS Selection
    cprint(Colors.CYAN, '\n═══ TTS (Text-to-Speech) ═══');
    console.log('\nDostępne providery:');
    
    const ttsOptions = Object.entries(TTS_PROVIDERS);
    for (let i = 0; i < ttsOptions.length; i++) {
        const [name, provider] = ttsOptions[i];
        const [available, reason] = provider.isAvailable(info);
        const status = available ? `${Colors.GREEN}✅` : `${Colors.YELLOW}⚠️`;
        const canRun = info.ramGb >= provider.minRamGb;
        const runStatus = canRun ? `${Colors.GREEN}(OK)` : `${Colors.RED}(za słaby sprzęt)`;
        
        console.log(`  ${status} ${i + 1}. ${provider.name}${Colors.NC} - ${provider.description}`);
        console.log(`      Wymagania: RAM≥${provider.minRamGb}GB ${runStatus}${Colors.NC}`);
        console.log(`      Status: ${reason}`);
    }
    
    console.log();
    while (true) {
        const choice = await question(rl, `Wybierz TTS (1-${ttsOptions.length}, ENTER=skip): `);
        if (!choice) break;
        
        const idx = parseInt(choice) - 1;
        if (idx >= 0 && idx < ttsOptions.length) {
            const [name, provider] = ttsOptions[idx];
            const [available] = provider.isAvailable(info);
            
            if (!available) {
                const install = await question(rl, `📦 ${provider.name} nie jest zainstalowany. Zainstalować? (y/n): `);
                if (install.toLowerCase() === 'y') {
                    await provider.install(info);
                }
            }
            
            config.tts_provider = name;
            break;
        }
        cprint(Colors.RED, '❌ Nieprawidłowy wybór');
    }
    
    rl.close();
    
    saveConfig(config);
    cprint(Colors.GREEN, `\n✅ Konfiguracja zapisana do ${CONFIG_FILE}`);
    
    return config;
}

// ═══════════════════════════════════════════════════════════════════════════════
// VOICE SHELL
// ═══════════════════════════════════════════════════════════════════════════════

async function speak(text, config) {
    const provider = config.tts_provider && TTS_PROVIDERS[config.tts_provider];
    if (provider && config.auto_tts) {
        const voice = config.tts_voice || 'pl';
        if (provider.speak.constructor.name === 'AsyncFunction') {
            await provider.speak(text.slice(0, 200), voice);
        } else {
            provider.speak(text.slice(0, 200), voice);
        }
    }
}

async function listen(config) {
    const provider = config.stt_provider && STT_PROVIDERS[config.stt_provider];
    if (!provider) {
        cprint(Colors.YELLOW, '⚠️  STT nie skonfigurowany. Uruchom: ./stts.mjs --setup');
        return '';
    }
    
    const audioPath = recordAudio(config.timeout || 5);
    if (!audioPath) return '';
    
    cprint(Colors.YELLOW, '🔄 Rozpoznawanie... ', false);
    const text = await provider.transcribe(audioPath, config.stt_model, config.language || 'pl');
    
    if (text) {
        cprint(Colors.GREEN, `✅ "${text}"`);
    } else {
        cprint(Colors.RED, '❌ Nie rozpoznano');
    }
    
    return text;
}

function runCommand(cmd) {
    return new Promise((resolve) => {
        try {
            const result = execSync(cmd, { encoding: 'utf8', timeout: 60000, stdio: ['pipe', 'pipe', 'pipe'], maxBuffer: 10 * 1024 * 1024 });
            resolve({ output: result, code: 0 });
        } catch (e) {
            resolve({ output: e.stdout || e.stderr || e.message, code: e.status || 1 });
        }
    });
}

async function voiceShell(config) {
    const PS1 = `${Colors.GREEN}🔊 stts>${Colors.NC} `;
    
    cprint(Colors.BOLD + Colors.CYAN, `
╔═══════════════════════════════════════════════════════════════════╗
║                    🎙️  STTS - Voice Shell (Node.js)               ║
╚═══════════════════════════════════════════════════════════════════╝
`);
    
    const sttProvider = config.stt_provider && STT_PROVIDERS[config.stt_provider];
    const ttsProvider = config.tts_provider && TTS_PROVIDERS[config.tts_provider];
    
    if (sttProvider) {
        cprint(Colors.GREEN, `  STT: ${sttProvider.name} (model: ${config.stt_model || 'default'})`);
    } else {
        cprint(Colors.YELLOW, '  STT: nie skonfigurowany (uruchom: ./stts.mjs --setup)');
    }
    
    if (ttsProvider) {
        cprint(Colors.GREEN, `  TTS: ${ttsProvider.name}`);
    } else {
        cprint(Colors.YELLOW, '  TTS: nie skonfigurowany');
    }
    
    console.log("\n  Komendy: ENTER=STT, 'exit'=wyjście, 'setup'=konfiguracja\n");
    
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    
    const prompt = () => {
        rl.question(PS1, async (cmd) => {
            cmd = cmd.trim();
            
            if (['exit', 'quit', 'q'].includes(cmd)) {
                cprint(Colors.CYAN, '\n👋 Do widzenia!');
                rl.close();
                return;
            }
            
            if (cmd === 'setup') {
                rl.close();
                config = await interactiveSetup();
                await voiceShell(config);
                return;
            }
            
            // Empty = STT
            if (!cmd) {
                cmd = await listen(config);
                if (!cmd) {
                    prompt();
                    return;
                }
            }
            
            // Run command
            cprint(Colors.BLUE, `▶️  ${cmd}`);
            const { output, code } = await runCommand(cmd);
            
            if (output.trim()) {
                console.log(output);
            }
            
            // TTS last line
            const lines = output.split('\n').filter(l => l.trim());
            if (lines.length) {
                const lastLine = lines[lines.length - 1].trim();
                if (lastLine !== cmd && lastLine.length > 3) {
                    cprint(Colors.MAGENTA, `📢 ${lastLine.slice(0, 80)}`);
                    await speak(lastLine, config);
                }
            }
            
            if (code !== 0) {
                cprint(Colors.RED, `❌ Exit code: ${code}`);
            }
            
            prompt();
        });
    };
    
    prompt();
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMMAND WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

async function runWithVoice(args, config) {
    const cmd = args.join(' ');
    cprint(Colors.GREEN, `🚀 ${cmd}`);
    
    const { output, code } = await runCommand(cmd);
    
    if (output.trim()) {
        console.log(output);
    }
    
    // TTS last line
    const lines = output.split('\n').filter(l => l.trim());
    if (lines.length) {
        const lastLine = lines[lines.length - 1].trim();
        cprint(Colors.MAGENTA, `📢 ${lastLine.slice(0, 80)}`);
        await speak(lastLine, config);
    }
    
    return code;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main() {
    let config = loadConfig();
    const args = process.argv.slice(2);

    if (args.includes('--version') || args.includes('-V')) {
        console.log(__version__);
        return;
    }
    
    // First run - setup
    if (!config.stt_provider && !config.tts_provider) {
        if (args.length === 0 || args.includes('--setup')) {
            config = await interactiveSetup();
        }
    }
    
    if (args.length === 0) {
        await voiceShell(config);
    } else if (args.includes('--setup')) {
        await interactiveSetup();
    } else if (args.includes('--help') || args.includes('-h')) {
        console.log(`
stts.mjs - Universal STT/TTS Shell Wrapper (Node.js)

Usage:
    ./stts.mjs                  # Interactive voice shell
    ./stts.mjs --setup          # Configure STT/TTS providers
    ./stts.mjs [cmd] [args]     # Run command with voice output

Opcje:
    --setup    Konfiguracja STT/TTS
    --version  Pokaż wersję
    --help     Ta pomoc

Przykłady:
    ./stts.mjs                  # Voice shell
    ./stts.mjs make build       # Uruchom z głosowym output
    ./stts.mjs python script.py # Dowolna komenda
`);
    } else {
        const code = await runWithVoice(args, config);
        process.exit(code);
    }
}

main().catch(console.error);
