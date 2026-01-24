#!/usr/bin/env node
/**
 * stts (nodejs) - Universal STT/TTS Shell Wrapper (Node.js ESM)
 *
 * Usage:
 *   ./stts.mjs                   # Interactive voice shell
 *   ./stts.mjs --setup           # Configure STT/TTS providers
 *   ./stts.mjs [cmd] [args...]   # Run command with voice output
 *
 * Testing / simulation:
 *   ./stts.mjs --stt-file file.wav --stt-only
 *   ./stts.mjs --stt-file file.wav            # transcribe and execute
 *
 * Notes:
 *   - Config stored in ~/.config/stts-nodejs/
 */

import { spawn, execSync, spawnSync } from 'node:child_process';
import { platform, homedir, cpus, totalmem, arch } from 'node:os';
import { readFileSync, writeFileSync, existsSync, mkdirSync, unlinkSync, chmodSync, statSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { get as httpsGet } from 'node:https';
import { createWriteStream } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

function loadDotenv() {
    const candidates = [];
    try {
        const here = dirname(fileURLToPath(import.meta.url));
        candidates.push(join(process.cwd(), '.env'));
        candidates.push(join(here, '.env'));
        candidates.push(join(here, '..', '.env'));
    } catch {}

    for (const p of candidates) {
        try {
            if (!existsSync(p)) continue;
            const txt = readFileSync(p, 'utf8');
            for (const line of txt.split(/\r?\n/)) {
                let s = line.trim();
                if (!s || s.startsWith('#')) continue;
                if (s.toLowerCase().startsWith('export ')) s = s.slice(7).trim();
                const idx = s.indexOf('=');
                if (idx <= 0) continue;
                const k = s.slice(0, idx).trim();
                let v = s.slice(idx + 1).trim();
                if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
                    v = v.slice(1, -1);
                }
                if (!k) continue;
                if (process.env[k] === undefined) process.env[k] = v;
            }
            break;
        } catch {}
    }
}

loadDotenv();

const CONFIG_DIR = process.env.STTS_CONFIG_DIR
    ? process.env.STTS_CONFIG_DIR
    : join(homedir(), '.config', 'stts-nodejs');
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

function applyEnvOverrides(config) {
    if (process.env.STTS_TIMEOUT) {
        const n = Number(process.env.STTS_TIMEOUT);
        if (Number.isFinite(n)) config.timeout = n;
    }
    if (process.env.STTS_LANGUAGE) config.language = String(process.env.STTS_LANGUAGE).trim() || config.language;
    if (process.env.STTS_TTS_VOICE) config.tts_voice = String(process.env.STTS_TTS_VOICE).trim() || config.tts_voice;
    return config;
}

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

function nlp2cmdTranslate(text) {
    const enabled = String(process.env.STTS_NLP2CMD_ENABLED || '0').trim().toLowerCase();
    if (!['1', 'true', 'yes', 'y'].includes(enabled)) return null;

    const bin = process.env.STTS_NLP2CMD_BIN || 'nlp2cmd';
    const args = (process.env.STTS_NLP2CMD_ARGS || '-r').split(/\s+/).filter(Boolean);

    const res = spawnSync(bin, [...args, text], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const out = String(res.stdout || '') + String(res.stderr || '');
    const lines = out.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return null;

    // heuristic: first plausible command line
    for (const l of lines) {
        if (l.startsWith('```')) continue;
        if (l.startsWith('📊')) continue;
        if (/^\$\s/.test(l)) return l.replace(/^\$\s*/, '');
        if (/[;&|]/.test(l) || l.includes(' ') || /^[a-zA-Z0-9_-]+$/.test(l)) return l;
    }
    return lines[0];
}

function nlp2cmdConfirm(cmd) {
    const confirm = String(process.env.STTS_NLP2CMD_CONFIRM || '1').trim().toLowerCase();
    if (['0', 'false', 'no', 'n'].includes(confirm)) return true;
    process.stdout.write(`\nNLP2CMD → ${cmd}\n`);
    const ans = spawnSync(process.platform === 'win32' ? 'cmd' : 'bash', ['-lc', 'read -r -p "Uruchomić tę komendę? (y/n): " a; echo $a'], { encoding: 'utf8' });
    const a = String(ans.stdout || '').trim().toLowerCase();
    return a === 'y';
}

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

function detectSystem() {
    const osName = platform();
    const archName = arch();
    const cpuCores = cpus().length;
    const ramGb = Math.round(totalmem() / 1024 / 1024 / 1024 * 10) / 10;

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

    let isRpi = false;
    try {
        if (osName === 'linux' && existsSync('/proc/device-tree/model')) {
            const model = readFileSync('/proc/device-tree/model', 'utf8');
            isRpi = model.toLowerCase().includes('raspberry');
        }
    } catch {}

    let hasMic = false;
    try {
        if (osName === 'linux') {
            const result = execSync('arecord -l', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
            hasMic = result.toLowerCase().includes('card');
        } else {
            hasMic = true;
        }
    } catch {}

    return {
        osName,
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

function downloadFile(url, destPath) {
    return new Promise((resolve, reject) => {
        ensureDir(dirname(destPath));
        const file = createWriteStream(destPath);

        const request = (u) => {
            httpsGet(u, (response) => {
                if (response.statusCode === 302 || response.statusCode === 301) {
                    request(response.headers.location);
                    return;
                }

                const totalSize = parseInt(response.headers['content-length'], 10);
                let downloaded = 0;

                response.on('data', (chunk) => {
                    downloaded += chunk.length;
                    const percent = totalSize ? Math.round((downloaded / totalSize) * 100) : 0;
                    process.stdout.write(`\r  Progress: ${percent}%`);
                });

                response.pipe(file);
                file.on('finish', () => {
                    file.close();
                    console.log();
                    resolve(destPath);
                });
            }).on('error', (err) => {
                try {
                    unlinkSync(destPath);
                } catch {}
                reject(err);
            });
        };

        request(url);
    });
}

function loadConfig() {
    ensureDir(CONFIG_DIR);
    if (existsSync(CONFIG_FILE)) {
        try {
            const cfg = { ...DEFAULT_CONFIG, ...JSON.parse(readFileSync(CONFIG_FILE, 'utf8')) };
            return applyEnvOverrides(cfg);
        } catch {}
    }
    return applyEnvOverrides({ ...DEFAULT_CONFIG });
}

function saveConfig(config) {
    ensureDir(CONFIG_DIR);
    writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

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

            const alreadyBuilt = [
                join(whisperDir, 'build', 'bin', 'whisper-cli'),
                join(whisperDir, 'build', 'bin', 'main'),
                join(whisperDir, 'main'),
            ].some((p) => existsSync(p));
            if (alreadyBuilt) {
                cprint(Colors.GREEN, '✅ whisper.cpp already installed!');
                return true;
            }

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
            const modelInfo = STT_PROVIDERS.whisper_cpp.models.find((m) => m[0] === modelName);
            if (!modelInfo) {
                cprint(Colors.RED, `❌ Unknown model: ${modelName}`);
                return null;
            }

            const [name, url, size] = modelInfo;
            const expectedBytes = Math.floor(Number(size) * 1024 * 1024 * 1024);
            const goodSize = (p) => {
                try {
                    const n = statSync(p).size;
                    return Number.isFinite(n) && n > Math.max(1024 * 1024, Math.floor(expectedBytes * 0.9));
                } catch {
                    return false;
                }
            };
            let modelPath;
            if (name === 'large') {
                const p2 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large-v3.bin');
                const p1 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large.bin');
                if (existsSync(p2) && goodSize(p2)) return p2;
                if (existsSync(p1) && goodSize(p1)) return p1;
                modelPath = p2;
            } else {
                modelPath = join(MODELS_DIR, 'whisper.cpp', `ggml-${name}.bin`);
            }

            if (existsSync(modelPath) && goodSize(modelPath)) {
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
                const candidates = [
                    join(MODELS_DIR, 'whisper.cpp', 'build', 'bin', 'whisper-cli'),
                    join(MODELS_DIR, 'whisper.cpp', 'build', 'bin', 'main'),
                    join(MODELS_DIR, 'whisper.cpp', 'main'),
                ];
                whisperBin = candidates.find((p) => existsSync(p)) || join(MODELS_DIR, 'whisper.cpp', 'main');
            }

            const modelName = model || 'base';
            let modelPath;
            if (modelName === 'large') {
                const p2 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large-v3.bin');
                const p1 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large.bin');
                modelPath = existsSync(p2) ? p2 : p1;
            } else {
                modelPath = join(MODELS_DIR, 'whisper.cpp', `ggml-${modelName}.bin`);
            }
            if (!existsSync(modelPath)) {
                await STT_PROVIDERS.whisper_cpp.downloadModel(modelName);
                if (modelName === 'large') {
                    const p2 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large-v3.bin');
                    const p1 = join(MODELS_DIR, 'whisper.cpp', 'ggml-large.bin');
                    modelPath = existsSync(p2) ? p2 : p1;
                } else {
                    modelPath = join(MODELS_DIR, 'whisper.cpp', `ggml-${modelName}.bin`);
                }
            }

            try {
                const result = execSync(
                    `"${whisperBin}" -m "${modelPath}" -l ${language} -f "${audioPath}" -nt`,
                    { encoding: 'utf8', timeout: 120000, stdio: ['pipe', 'pipe', 'pipe'] }
                );
                return result.trim();
            } catch (e) {
                cprint(Colors.RED, `❌ Transcription error: ${e.message}`);
                return '';
            }
        },
    },
};

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
};

function recordAudio(duration = 5, outputPath = '/tmp/stts_audio.wav') {
    const info = detectSystem();
    cprint(Colors.GREEN, `🎤 Mów (${duration}s)... `, false);

    try {
        if (info.osName === 'linux') {
            execSync(`arecord -d ${duration} -f cd -t wav "${outputPath}"`, { stdio: 'ignore', timeout: (duration + 2) * 1000 });
        } else {
            cprint(Colors.RED, '❌ Recording supported only on Linux in this minimal build');
            return '';
        }
        console.log('✅');
        return outputPath;
    } catch (e) {
        cprint(Colors.RED, `❌ Recording failed: ${e.message}`);
        return '';
    }
}

async function question(rl, prompt) {
    return new Promise((resolve) => rl.question(prompt, resolve));
}

async function interactiveSetup() {
    const config = loadConfig();
    const info = detectSystem();

    cprint(Colors.BOLD + Colors.CYAN, `\nSTTS (nodejs) - Setup\n`);
    printSystemInfo(info);

    const rl = createInterface({ input: process.stdin, output: process.stdout });

    const stt = STT_PROVIDERS.whisper_cpp;
    const [available, reason] = stt.isAvailable();
    console.log(`\nSTT: ${stt.name} (${reason})`);
    if (!available) {
        const install = await question(rl, 'Install whisper.cpp now? (y/n): ');
        if (install.toLowerCase() === 'y') {
            await stt.install(info);
        }
    }

    const recModel = stt.getRecommendedModel(info);
    const model = (await question(rl, `Whisper model [tiny/base/small/medium/large] (ENTER=${recModel}): `)) || recModel;
    config.stt_provider = 'whisper_cpp';
    config.stt_model = model;

    const download = await question(rl, `Download model ${model} now? (y/n): `);
    if (download.toLowerCase() === 'y') {
        await stt.downloadModel(model);
    }

    const tts = TTS_PROVIDERS.espeak;
    const [ttsAvail, ttsReason] = tts.isAvailable(info);
    console.log(`\nTTS: ${tts.name} (${ttsReason})`);
    if (!ttsAvail) {
        cprint(Colors.YELLOW, 'Install espeak: sudo apt install espeak');
        config.tts_provider = null;
    } else {
        config.tts_provider = 'espeak';
    }

    saveConfig(config);
    cprint(Colors.GREEN, `\n✅ Konfiguracja zapisana do ${CONFIG_FILE}`);

    rl.close();
    return config;
}

async function speak(text, config) {
    if (!config.auto_tts) return;
    const provider = config.tts_provider && TTS_PROVIDERS[config.tts_provider];
    if (!provider) return;

    const voice = config.tts_voice || 'pl';
    provider.speak(text.slice(0, 200), voice);
}

async function listen(config, sttFile = null) {
    const audioPath = sttFile || recordAudio(config.timeout || 5);
    if (!audioPath) return '';

    if (process.env.STTS_MOCK_STT === '1') {
        const sidecar = `${audioPath}.txt`;
        if (existsSync(sidecar)) {
            try {
                return readFileSync(sidecar, 'utf8').trim();
            } catch {
                return '';
            }
        }
    }

    const provider = config.stt_provider && STT_PROVIDERS[config.stt_provider];
    if (!provider) {
        cprint(Colors.YELLOW, '⚠️  STT nie skonfigurowany. Uruchom: ./stts.mjs --setup');
        return '';
    }

    cprint(Colors.YELLOW, '🔄 Rozpoznawanie... ', false);
    const text = await provider.transcribe(audioPath, config.stt_model, config.language || 'pl');

    if (text) {
        cprint(Colors.GREEN, `✅ "${text}"`);
    } else {
        cprint(Colors.RED, '❌ Nie rozpoznano');
    }

    return text;
}

async function runCommand(cmd) {
    try {
        const out = execSync(cmd, { encoding: 'utf8', timeout: 60000, stdio: ['pipe', 'pipe', 'pipe'], maxBuffer: 10 * 1024 * 1024 });
        return { output: out, code: 0 };
    } catch (e) {
        return { output: e.stdout || e.stderr || e.message, code: e.status || 1 };
    }
}

async function voiceShell(config) {
    const PS1 = `${Colors.GREEN}🔊 stts(node)>[0m `;

    cprint(Colors.BOLD + Colors.CYAN, `\nSTTS (nodejs) - Voice Shell\n`);
    console.log("Komendy: ENTER=STT, 'exit'=wyjście, 'setup'=konfiguracja\n");

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

            if (cmd.startsWith('nlp ')) {
                const nl = cmd.slice(4).trim();
                if (!nl) {
                    prompt();
                    return;
                }
                const translated = nlp2cmdTranslate(nl);
                if (!translated || !nlp2cmdConfirm(translated)) {
                    prompt();
                    return;
                }
                cmd = translated;
            }

            if (!cmd) {
                cmd = await listen(config);
                if (!cmd) {
                    prompt();
                    return;
                }
                const translated = nlp2cmdTranslate(cmd);
                if (translated && nlp2cmdConfirm(translated)) {
                    cmd = translated;
                }
            }

            cprint(Colors.BLUE, `▶️  ${cmd}`);
            const { output, code } = await runCommand(cmd);
            if (output.trim()) console.log(output);

            const lines = output.split('\n').filter((l) => l.trim());
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

function parseArgs(argv) {
    let sttFile = null;
    let sttOnly = false;
    let setup = false;
    let help = false;
    const rest = [];

    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--stt-file') {
            sttFile = argv[i + 1] || null;
            i++;
        } else if (a === '--stt-only') {
            sttOnly = true;
        } else if (a === '--setup') {
            setup = true;
        } else if (a === '--help' || a === '-h') {
            help = true;
        } else {
            rest.push(a);
        }
    }

    return { sttFile, sttOnly, setup, help, rest };
}

async function main() {
    let config = loadConfig();
    const { sttFile, sttOnly, setup, help, rest } = parseArgs(process.argv.slice(2));

    if (help) {
        console.log(`${readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(0, 14).join('\n')}\n`);
        console.log('Options:');
        console.log('  --setup             configure STT/TTS');
        console.log('  --stt-file PATH     use WAV file instead of recording');
        console.log('  --stt-only          only transcribe (do not execute)');
        return;
    }

    if (setup || (!config.stt_provider && !config.tts_provider && !sttFile && rest.length === 0)) {
        config = await interactiveSetup();
    }

    if (sttFile) {
        const shellText = await listen(config, sttFile);
        if (sttOnly) {
            console.log(shellText);
            process.exit(shellText ? 0 : 1);
        }
        if (!shellText) process.exit(1);
        let cmd = shellText;
        const translated = nlp2cmdTranslate(cmd);
        if (translated && nlp2cmdConfirm(translated)) cmd = translated;
        const { output, code } = await runCommand(cmd);
        if (output.trim()) console.log(output);
        process.exit(code);
    }

    if (rest.length === 0) {
        await voiceShell(config);
        return;
    }

    const cmd = rest.join(' ');
    const { output, code } = await runCommand(cmd);
    if (output.trim()) console.log(output);

    const lines = output.split('\n').filter((l) => l.trim());
    if (lines.length) {
        await speak(lines[lines.length - 1].trim(), config);
    }

    process.exit(code);
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
