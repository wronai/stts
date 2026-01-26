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
const CONFIG_FILE_JSON = join(CONFIG_DIR, 'config.json');
const CONFIG_FILE_YAML = join(CONFIG_DIR, 'config.yaml');
const CONFIG_FILE_YML = join(CONFIG_DIR, 'config.yml');
const MODELS_DIR = join(CONFIG_DIR, 'models');
const HISTORY_FILE = join(CONFIG_DIR, 'history');

const DEFAULT_CONFIG = {
    stt_provider: null,
    tts_provider: null,
    stt_model: null,
    stt_gpu_layers: 0,
    tts_voice: 'pl',
    language: 'pl',
    timeout: 5,
    auto_tts: true,
    stream_cmd: false,
    fast_start: true,
    nlp2cmd_parallel: false,
};

function applyEnvOverrides(config) {
    if (process.env.STTS_TIMEOUT) {
        const n = Number(process.env.STTS_TIMEOUT);
        if (Number.isFinite(n)) config.timeout = n;
    }
    if (process.env.STTS_LANGUAGE) config.language = String(process.env.STTS_LANGUAGE).trim() || config.language;
    if (process.env.STTS_STT_PROVIDER) {
        let v = String(process.env.STTS_STT_PROVIDER).trim();
        if (v === 'whisper' || v === 'whisper.cpp') v = 'whisper_cpp';
        config.stt_provider = v || null;
    }
    if (process.env.STTS_STT_MODEL) {
        const v = String(process.env.STTS_STT_MODEL).trim();
        config.stt_model = v || null;
    }
    if (process.env.STTS_STT_GPU_LAYERS) {
        const n = Number(String(process.env.STTS_STT_GPU_LAYERS).trim());
        if (Number.isFinite(n)) config.stt_gpu_layers = Math.max(0, Math.floor(n));
    }
    if (process.env.STTS_TTS_PROVIDER) {
        let v = String(process.env.STTS_TTS_PROVIDER).trim();
        if (v === 'espeak-ng') v = 'espeak';
        config.tts_provider = v || null;
    }
    if (process.env.STTS_TTS_VOICE) config.tts_voice = String(process.env.STTS_TTS_VOICE).trim() || config.tts_voice;
    if (process.env.STTS_AUTO_TTS) {
        const v = String(process.env.STTS_AUTO_TTS).trim().toLowerCase();
        config.auto_tts = !['0', 'false', 'no', 'n'].includes(v);
    }
    if (process.env.STTS_STREAM) {
        const v = String(process.env.STTS_STREAM).trim().toLowerCase();
        config.stream_cmd = !['0', 'false', 'no', 'n'].includes(v);
    }
    if (process.env.STTS_FAST_START) {
        const v = String(process.env.STTS_FAST_START).trim().toLowerCase();
        config.fast_start = !['0', 'false', 'no', 'n'].includes(v);
    }
    if (process.env.STTS_NLP2CMD_PARALLEL) {
        const v = String(process.env.STTS_NLP2CMD_PARALLEL).trim().toLowerCase();
        config.nlp2cmd_parallel = !['0', 'false', 'no', 'n'].includes(v);
    }
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

const SHELL_CORRECTIONS = {
    'el es': 'ls',
    'el s': 'ls',
    'lista': 'ls',
    'l s': 'ls',
    'kopi': 'cp',
    'kopiuj': 'cp',
    'przenieś': 'mv',
    'usuń': 'rm',
    'katalog': 'mkdir',
    'pokaż': 'cat',
    'edytuj': 'nano',
    'eko': 'echo',
    'cd..': 'cd ..',
    'git pusz': 'git push',
    'git pul': 'git pull',
    'pip instal': 'pip install',
    'sudo apt instal': 'sudo apt install',
};

const PHONETIC_EN_CORRECTIONS = {
    'serwer': 'server', 'servera': 'server', 'serwera': 'server', 'serwerze': 'server', 'serwery': 'servers',
    'endżineks': 'nginx', 'endżinks': 'nginx', 'enginx': 'nginx', 'engines': 'nginx',
    'endżin': 'engine', 'endżiny': 'engines',
    'dokker': 'docker', 'doker': 'docker', 'dockera': 'docker', 'dokera': 'docker',
    'kubernetis': 'kubernetes', 'kubernitis': 'kubernetes',
    'kej eight': 'k8s', 'kej ejtis': 'k8s', 'kej ejts': 'k8s', 'kej8s': 'k8s',
    'kubektl': 'kubectl', 'kubkontrol': 'kubectl', 'kubctl': 'kubectl',
    'postgresem': 'postgres', 'postgresom': 'postgres', 'postgresa': 'postgres', 'postgressa': 'postgres',
    'eskuel': 'sql', 'es kju el': 'sql', 'eskjuel': 'sql',
    'majeskuel': 'mysql', 'majsql': 'mysql', 'mysquel': 'mysql',
    'mongo di bi': 'mongodb', 'mongodi': 'mongodb', 'mongołdi': 'mongodb',
    'redisa': 'redis', 'redys': 'redis',
    'elastik': 'elastic', 'elastiksercz': 'elasticsearch',
    'apacz': 'apache', 'apatche': 'apache', 'apacze': 'apache',
    'nodżejejs': 'nodejs', 'noddżejs': 'nodejs', 'nodżs': 'nodejs', 'node dżejs': 'nodejs', 'nodjs': 'nodejs',
    'piton': 'python', 'pajton': 'python', 'pajtona': 'python', 'pytona': 'python',
    'dżawa': 'java', 'dżawy': 'java', 'dżawą': 'java',
    'dżawaskrypt': 'javascript', 'jawa skrypt': 'javascript',
    'dżejs': 'js', 'jst': 'js',
    'tajpskrypt': 'typescript', 'tajp skrypt': 'typescript',
    'reakt': 'react', 'reakta': 'react',
    'wju': 'vue', 'wjuejs': 'vuejs',
    'angulara': 'angular', 'angularem': 'angular',
    'netflajs': 'nextjs', 'nekst dżejs': 'nextjs',
    'ekspres': 'express', 'ekspresa': 'express',
    'flaskem': 'flask',
    'dżango': 'django', 'dżanga': 'django',
    'larawel': 'laravel',
    'symfonią': 'symfony',
    'springa': 'spring', 'springbutem': 'springboot',
    'majkroserwisy': 'microservices', 'majkroservisy': 'microservices', 'mikroserwisy': 'microservices',
    'rest ejpi aj': 'rest api', 'restejpiaj': 'rest api',
    'dżejson': 'json', 'jsoń': 'json',
    'jaml': 'yaml', 'jamł': 'yaml',
    'tomł': 'toml',
    'deploj': 'deploy', 'deplojuj': 'deploy', 'deplojem': 'deploy',
    'deploymenta': 'deployment', 'deploimentu': 'deployment',
    'bilda': 'build', 'bildem': 'build', 'bilduj': 'build',
    'starta': 'start', 'startuj': 'start',
    'restarta': 'restart', 'restartuj': 'restart',
    'stopa': 'stop', 'stopuj': 'stop',
    'testa': 'test', 'testuj': 'test',
    'lintuj': 'lint', 'lintera': 'linter',
    'awsa': 'aws', 'awsie': 'aws', 'ejdablju es': 'aws',
    'azura': 'azure', 'ejżur': 'azure',
    'dżi si pi': 'gcp',
    'wercel': 'vercel', 'wersela': 'vercel',
    'terraforma': 'terraform', 'teraform': 'terraform',
    'ansibla': 'ansible', 'ansiblem': 'ansible',
    'dżenkinsem': 'jenkins', 'dżenkinsa': 'jenkins', 'jenkinsa': 'jenkins',
    'siajaidi': 'ci/cd', 'ci cd': 'ci/cd', 'si aj si di': 'ci/cd',
    'githuba': 'github', 'gitlaba': 'gitlab', 'gitłab': 'gitlab',
    'bitketa': 'bitbucket', 'bitbaketa': 'bitbucket',
    'prullrikłest': 'pull request', 'pul rekłest': 'pull request', 'pul rikłest': 'pull request',
    'merdż': 'merge', 'merdżuj': 'merge',
    'brenczem': 'branch', 'brancz': 'branch', 'brencza': 'branch',
    'komitta': 'commit', 'komituj': 'commit', 'komitem': 'commit',
    'kontejnera': 'container', 'kontejner': 'container', 'kontener': 'container', 'kontenera': 'container',
    'imidża': 'image', 'imidż': 'image', 'imidżem': 'image',
    'wolumena': 'volume', 'wolumen': 'volume',
    'networkiem': 'network', 'sieć': 'network', 'sieci': 'network',
    'serwisem': 'service', 'serwisy': 'services', 'serwis': 'service',
    'podów': 'pods', 'pody': 'pods', 'podem': 'pod',
    'namespacie': 'namespace', 'nejmspejs': 'namespace',
    'helma': 'helm', 'helmem': 'helm',
    'prometheusa': 'prometheus', 'prometeus': 'prometheus',
    'grafaną': 'grafana', 'kibaną': 'kibana',
    'logstashem': 'logstash', 'logstasz': 'logstash',
    'rabit em kju': 'rabbitmq',
    'kafką': 'kafka', 'kafki': 'kafka', 'kafkem': 'kafka',
    'selerym': 'celery',
};

const REGEX_FIXES = [
    [/\bel\s+es\b/gi, 'ls'],
    [/\bel\s+s\b/gi, 'ls'],
    [/\bl\s+s\b/gi, 'ls'],
    [/\bgit\s+stat\b/gi, 'git status'],
    [/\bgit\s+pusz\b/gi, 'git push'],
    [/\bgit\s+pul\b/gi, 'git pull'],
    [/\bgrepp?\b/gi, 'grep'],
    [/\bsudo\s+apt\s+instal\b/gi, 'sudo apt install'],
    [/\bpip\s+instal\b/gi, 'pip install'],
    [/\beko\s+/gi, 'echo '],
    [/\bkopi\s+/gi, 'cp '],
    [/\bmkdir\s+-p\s*/gi, 'mkdir -p '],
    [/\bservera?\s+engines?\b/gi, 'nginx server'],
    [/\bserwera?\s+engines?\b/gi, 'nginx server'],
    [/\bserwer\s+endżi?n?e?ks?\b/gi, 'nginx server'],
    [/\bdocker\s+kompo[uz]e?\b/gi, 'docker compose'],
    [/\bdocker\s+kompoza?\b/gi, 'docker compose'],
    [/\bdokker\s+kompo[uz]e?\b/gi, 'docker compose'],
    [/\bkube?r?netis\b/gi, 'kubernetes'],
    [/\bkube?rnitis\b/gi, 'kubernetes'],
];

const PHONETIC_KEYS = Object.keys(PHONETIC_EN_CORRECTIONS);
const FUZZY_CACHE = new Map();

function levenshteinBounded(a, b, maxDist) {
    if (a === b) return 0;
    const al = a.length;
    const bl = b.length;
    if (Math.abs(al - bl) > maxDist) return maxDist + 1;
    if (al === 0) return bl;
    if (bl === 0) return al;

    let prev = new Array(bl + 1);
    let cur = new Array(bl + 1);
    for (let j = 0; j <= bl; j++) prev[j] = j;

    for (let i = 1; i <= al; i++) {
        cur[0] = i;
        let rowMin = cur[0];
        const ca = a.charCodeAt(i - 1);
        for (let j = 1; j <= bl; j++) {
            const cost = ca === b.charCodeAt(j - 1) ? 0 : 1;
            const v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
            cur[j] = v;
            if (v < rowMin) rowMin = v;
        }
        if (rowMin > maxDist) return maxDist + 1;
        const tmp = prev;
        prev = cur;
        cur = tmp;
    }
    return prev[bl];
}

function fuzzyPhoneticReplacement(clean) {
    const s = String(clean || '').trim().toLowerCase();
    if (!s) return null;
    if (s.length < 4 || s.length > 18) return null;
    if (!/^[a-ząćęłńóśźż]+$/i.test(s)) return null;
    if (s.includes(' ')) return null;

    if (FUZZY_CACHE.has(s)) return FUZZY_CACHE.get(s);

    const maxDist = s.length <= 6 ? 1 : 2;
    let bestKey = null;
    let bestDist = maxDist + 1;

    for (const k of PHONETIC_KEYS) {
        if (k.includes(' ')) continue;
        if (k[0] !== s[0]) continue;
        if (Math.abs(k.length - s.length) > maxDist) continue;
        const d = levenshteinBounded(s, k, maxDist);
        if (d < bestDist) {
            bestDist = d;
            bestKey = k;
            if (bestDist === 0) break;
        }
    }

    const out = bestKey && bestDist <= maxDist ? PHONETIC_EN_CORRECTIONS[bestKey] : null;
    FUZZY_CACHE.set(s, out);
    if (FUZZY_CACHE.size > 4096) FUZZY_CACHE.clear();
    return out;
}

function fixPhoneticEnglish(text) {
    const words = text.split(/\s+/);
    const fixed = [];
    for (const word of words) {
        const lower = word.toLowerCase();
        const clean = lower.replace(/^[.,!?;:"'()\[\]{}]+|[.,!?;:"'()\[\]{}]+$/g, '');
        const direct = PHONETIC_EN_CORRECTIONS[clean];
        const fuzzy = direct ? null : fuzzyPhoneticReplacement(clean);
        const chosen = direct || fuzzy;
        if (chosen) {
            let replacement = chosen;
            if (word[0] && word[0] === word[0].toUpperCase()) {
                replacement = replacement.charAt(0).toUpperCase() + replacement.slice(1);
            }
            fixed.push(clean !== lower ? word.replace(clean, replacement) : replacement);
        } else {
            fixed.push(word);
        }
    }
    return fixed.join(' ');
}

function normalizeSTTText(text, language = 'pl') {
    if (!text) return '';
    
    let result = text.trim();
    
    result = result.replace(/[.,!?;:]+$/, '');
    
    for (const [pattern, replacement] of REGEX_FIXES) {
        result = result.replace(pattern, replacement);
    }
    
    result = fixPhoneticEnglish(result);
    
    const lower = result.toLowerCase().trim();
    for (const [wrong, correct] of Object.entries(SHELL_CORRECTIONS)) {
        if (lower === wrong) return correct;
    }
    
    return result;
}

function detectCuda() {
    try {
        execSync('nvcc --version', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], timeout: 5000 });
        return true;
    } catch {
        return false;
    }
}

function hasGpuBuild() {
    const marker = join(MODELS_DIR, 'whisper.cpp', '.gpu_build');
    return existsSync(marker);
}

function nlp2cmdParallelEnabled(config) {
    if (config && !!config.nlp2cmd_parallel) return true;
    const v = String(process.env.STTS_NLP2CMD_PARALLEL || '').trim().toLowerCase();
    return ['1', 'true', 'yes', 'y'].includes(v);
}

function resolveNlp2cmdPython() {
    const v = String(process.env.STTS_NLP2CMD_PYTHON || '').trim();
    return v || 'python3';
}

class Nlp2cmdWorker {
    constructor(pythonExe) {
        const code =
            `import sys, json\n` +
            `pipeline = None\nerr = None\n` +
            `try:\n` +
            `    from nlp2cmd.generation.pipeline import RuleBasedPipeline\n` +
            `    pipeline = RuleBasedPipeline(use_enhanced_context=False)\n` +
            `except Exception as e:\n` +
            `    err = str(e)\n` +
            `for line in sys.stdin:\n` +
            `    s = (line or '').strip()\n` +
            `    if not s:\n` +
            `        continue\n` +
            `    try:\n` +
            `        req = json.loads(s)\n` +
            `    except Exception:\n` +
            `        req = {'text': s}\n` +
            `    text = str(req.get('text', '') or '')\n` +
            `    if not pipeline:\n` +
            `        out = {'ok': False, 'command': '', 'error': err or 'nlp2cmd not available'}\n` +
            `    else:\n` +
            `        try:\n` +
            `            r = pipeline.process(text)\n` +
            `            cmd = (getattr(r, 'command', '') or '').strip()\n` +
            `            out = {'ok': bool(cmd), 'command': cmd, 'error': ''}\n` +
            `        except Exception as e:\n` +
            `            out = {'ok': False, 'command': '', 'error': str(e)}\n` +
            `    sys.stdout.write(json.dumps(out, ensure_ascii=False) + '\\n')\n` +
            `    sys.stdout.flush()\n`;

        const env = { ...process.env };
        if (env.NLP2CMD_USE_ENHANCED_CONTEXT === undefined) env.NLP2CMD_USE_ENHANCED_CONTEXT = '0';

        this.proc = spawn(pythonExe, ['-u', '-c', code], { stdio: ['pipe', 'pipe', 'ignore'], env });
        this._buf = '';
        this._queue = [];

        this.proc.stdout.on('data', (chunk) => {
            this._buf += String(chunk || '');
            while (true) {
                const idx = this._buf.indexOf('\n');
                if (idx < 0) break;
                const line = this._buf.slice(0, idx).trim();
                this._buf = this._buf.slice(idx + 1);
                const item = this._queue.shift();
                if (!item) continue;
                clearTimeout(item.t);
                let cmd = null;
                try {
                    const res = JSON.parse(line);
                    cmd = String(res.command || '').trim() || null;
                } catch {
                    cmd = null;
                }
                item.resolve(cmd);
            }
        });

        this.proc.on('exit', () => {
            for (const item of this._queue.splice(0)) {
                clearTimeout(item.t);
                item.resolve(null);
            }
        });
    }

    translate(text, timeoutMs = 20000) {
        const s = String(text || '').trim();
        if (!s) return Promise.resolve(null);
        if (!this.proc || this.proc.killed) return Promise.resolve(null);
        if (!this.proc.stdin) return Promise.resolve(null);

        return new Promise((resolve) => {
            const t = setTimeout(() => resolve(null), timeoutMs);
            this._queue.push({ resolve, t });
            try {
                this.proc.stdin.write(`${JSON.stringify({ text: s })}\n`);
            } catch {
                clearTimeout(t);
                this._queue.pop();
                resolve(null);
            }
        });
    }
}

let NLP2CMD_WORKER = null;

function nlp2cmdPrewarm(config) {
    if (!nlp2cmdParallelEnabled(config)) return;
    if (NLP2CMD_WORKER) return;
    try {
        NLP2CMD_WORKER = new Nlp2cmdWorker(resolveNlp2cmdPython());
    } catch {
        NLP2CMD_WORKER = null;
    }
}

async function nlp2cmdTranslate(text, { config = null, force = false } = {}) {
    if (!force) {
        const enabled = String(process.env.STTS_NLP2CMD_ENABLED || '0').trim().toLowerCase();
        if (!['1', 'true', 'yes', 'y'].includes(enabled)) return null;
    }

    text = normalizeSTTText(text || '', process.env.STTS_LANGUAGE || 'pl');

    if (nlp2cmdParallelEnabled(config)) {
        nlp2cmdPrewarm(config);
        if (NLP2CMD_WORKER) {
            const cmd = await NLP2CMD_WORKER.translate(text);
            if (cmd) return cmd;
        }
    }

    const bin = process.env.STTS_NLP2CMD_BIN || 'nlp2cmd';
    const args = (process.env.STTS_NLP2CMD_ARGS || '-r').split(/\s+/).filter(Boolean);
    const res = spawnSync(bin, [...args, text], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const out = String(res.stdout || '') + String(res.stderr || '');
    const lines = out.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return null;

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
    const ans = spawnSync(process.platform === 'win32' ? 'cmd' : 'bash', ['-c', 'read -r -p "Uruchomić tę komendę? (y/n): " a; echo $a'], { encoding: 'utf8' });
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

const PROMPT_FLAG_CACHE = new Map();

function detectPromptFlag(whisperBin) {
    const bin = String(whisperBin || '').trim();
    if (!bin) return null;
    if (PROMPT_FLAG_CACHE.has(bin)) return PROMPT_FLAG_CACHE.get(bin);
    let out = '';
    try {
        out = String(execSync(`"${bin}" --help`, { encoding: 'utf8', timeout: 2000, stdio: ['ignore', 'pipe', 'pipe'] }) || '');
    } catch (e) {
        out = String((e && e.stdout) || '') + String((e && e.stderr) || '');
    }
    let flag = null;
    if (out.includes('--prompt')) flag = '--prompt';
    else if (/^\s*-p\b.*prompt/im.test(out)) flag = '-p';
    PROMPT_FLAG_CACHE.set(bin, flag);
    if (PROMPT_FLAG_CACHE.size > 128) PROMPT_FLAG_CACHE.clear();
    return flag;
}

function ensureDir(dir) {
    if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
    }
}

function normalizeConfigFormat(v) {
    if (!v) return null;
    const s = String(v).trim().toLowerCase();
    if (s === 'yaml' || s === 'yml') return 'yaml';
    if (s === 'json') return 'json';
    return null;
}

function getConfigFileForLoad() {
    const fmt = normalizeConfigFormat(process.env.STTS_CONFIG_FORMAT);
    if (fmt === 'yaml') {
        if (existsSync(CONFIG_FILE_YAML)) return CONFIG_FILE_YAML;
        if (existsSync(CONFIG_FILE_YML)) return CONFIG_FILE_YML;
        return CONFIG_FILE_YAML;
    }
    if (fmt === 'json') return CONFIG_FILE_JSON;

    // auto: prefer yaml if present
    if (existsSync(CONFIG_FILE_YAML)) return CONFIG_FILE_YAML;
    if (existsSync(CONFIG_FILE_YML)) return CONFIG_FILE_YML;
    if (existsSync(CONFIG_FILE_JSON)) return CONFIG_FILE_JSON;
    return CONFIG_FILE_JSON;
}

function getConfigFileForSave() {
    const fmt = normalizeConfigFormat(process.env.STTS_CONFIG_FORMAT);
    if (fmt === 'yaml') {
        if (existsSync(CONFIG_FILE_YML) && !existsSync(CONFIG_FILE_YAML)) return CONFIG_FILE_YML;
        return CONFIG_FILE_YAML;
    }
    if (fmt === 'json') return CONFIG_FILE_JSON;

    if (existsSync(CONFIG_FILE_YAML)) return CONFIG_FILE_YAML;
    if (existsSync(CONFIG_FILE_YML)) return CONFIG_FILE_YML;
    if (existsSync(CONFIG_FILE_JSON)) return CONFIG_FILE_JSON;
    return CONFIG_FILE_JSON;
}

function parseSimpleYaml(text) {
    const out = {};
    for (const raw of String(text || '').split(/\r?\n/)) {
        const line = raw.trim();
        if (!line || line.startsWith('#')) continue;
        const idx = line.indexOf(':');
        if (idx <= 0) continue;
        const key = line.slice(0, idx).trim();
        if (!key) continue;
        const valS = line.slice(idx + 1).trim();
        if (!valS || valS === 'null' || valS === '~') {
            out[key] = null;
            continue;
        }
        if ((valS.startsWith('"') && valS.endsWith('"')) || (valS.startsWith("'") && valS.endsWith("'"))) {
            out[key] = valS.slice(1, -1);
            continue;
        }
        const low = valS.toLowerCase();
        if (['true', 'yes', 'y', 'on'].includes(low)) {
            out[key] = true;
            continue;
        }
        if (['false', 'no', 'n', 'off'].includes(low)) {
            out[key] = false;
            continue;
        }
        const num = Number(valS);
        if (Number.isFinite(num) && /^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(valS)) {
            out[key] = valS.includes('.') || /[eE]/.test(valS) ? num : parseInt(valS, 10);
            continue;
        }
        out[key] = valS;
    }
    return out;
}

function dumpSimpleYaml(data) {
    const fmt = (v) => {
        if (v === null || v === undefined) return 'null';
        if (typeof v === 'boolean') return v ? 'true' : 'false';
        if (typeof v === 'number') return String(v);
        const s = String(v);
        if (s === '') return '""';
        const needsQuote = /\s/.test(s) || /[:#"']/.test(s);
        if (needsQuote) return `"${s.replace(/\\/g, '\\\\').replace(/\"/g, '\\"')}"`;
        return s;
    };

    const keys = Object.keys(data || {}).filter((k) => typeof k === 'string').sort();
    return keys.map((k) => `${k}: ${fmt(data[k])}`).join('\n') + '\n';
}

let SYSTEM_INFO_CACHE_FAST = null;
let SYSTEM_INFO_CACHE_FULL = null;

function detectSystem({ fast = false } = {}) {
    if (fast && SYSTEM_INFO_CACHE_FAST) return SYSTEM_INFO_CACHE_FAST;
    if (!fast && SYSTEM_INFO_CACHE_FULL) return SYSTEM_INFO_CACHE_FULL;
    const osName = platform();
    const archName = arch();
    const cpuCores = cpus().length;
    const ramGb = Math.round(totalmem() / 1024 / 1024 / 1024 * 10) / 10;

    let gpuName = null;
    let gpuVramGb = null;
    if (!fast) {
        try {
            const result = execSync(
                'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits',
                { encoding: 'utf8', timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'] }
            );
            const parts = result.trim().split(', ');
            gpuName = parts[0];
            gpuVramGb = parts[1] ? Math.round(parseFloat(parts[1]) / 1024 * 10) / 10 : null;
        } catch {}
    }

    let isRpi = false;
    try {
        if (osName === 'linux' && existsSync('/proc/device-tree/model')) {
            const model = readFileSync('/proc/device-tree/model', 'utf8');
            isRpi = model.toLowerCase().includes('raspberry');
        }
    } catch {}

    let hasMic = false;
    if (!fast) {
        try {
            if (osName === 'linux') {
                const result = execSync('arecord -l', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
                hasMic = result.toLowerCase().includes('card');
            } else {
                hasMic = true;
            }
        } catch {}
    }

    const info = {
        osName,
        arch: archName,
        cpuCores,
        ramGb,
        gpuName,
        gpuVramGb,
        isRpi,
        hasMic,
    };

    if (fast) {
        SYSTEM_INFO_CACHE_FAST = info;
    } else {
        SYSTEM_INFO_CACHE_FULL = info;
    }
    return info;
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
    const cfg = { ...DEFAULT_CONFIG };
    const p = getConfigFileForLoad();
    if (p && existsSync(p)) {
        try {
            if (p.endsWith('.yaml') || p.endsWith('.yml')) {
                Object.assign(cfg, parseSimpleYaml(readFileSync(p, 'utf8')));
            } else {
                Object.assign(cfg, JSON.parse(readFileSync(p, 'utf8')));
            }
            return applyEnvOverrides(cfg);
        } catch {}
    }
    return applyEnvOverrides({ ...DEFAULT_CONFIG });
}

function saveConfig(config) {
    ensureDir(CONFIG_DIR);
    const p = getConfigFileForSave();
    if (p.endsWith('.yaml') || p.endsWith('.yml')) {
        writeFileSync(p, dumpSimpleYaml(config), 'utf8');
    } else {
        writeFileSync(p, JSON.stringify(config, null, 2), 'utf8');
    }
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

            const hasGpuBuild = () => existsSync(join(whisperDir, '.gpu_build'));
            const detectCuda = () => !!which('nvcc');

            const alreadyBuilt = [
                join(whisperDir, 'build', 'bin', 'whisper-cli'),
                join(whisperDir, 'build', 'bin', 'main'),
                join(whisperDir, 'main'),
            ].some((p) => existsSync(p));
            if (alreadyBuilt) {
                const gpuInfo = hasGpuBuild() ? ' (GPU)' : ' (CPU)';
                cprint(Colors.GREEN, `✅ whisper.cpp already installed!${gpuInfo}`);
                return true;
            }

            try {
                if (!existsSync(join(whisperDir, 'Makefile'))) {
                    execSync(`git clone https://github.com/ggerganov/whisper.cpp "${whisperDir}"`, { stdio: 'inherit' });
                }

                let useCuda = detectCuda();
                const envGpu = String(process.env.STTS_GPU_ENABLED || '').trim().toLowerCase();
                if (['1', 'true', 'yes'].includes(envGpu)) useCuda = true;
                else if (['0', 'false', 'no'].includes(envGpu)) useCuda = false;

                if (useCuda) {
                    cprint(Colors.GREEN, '🎮 CUDA detected - building with GPU support...');
                    const buildDir = join(whisperDir, 'build');
                    ensureDir(buildDir);
                    execSync('cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release', { cwd: buildDir, stdio: 'inherit' });
                    execSync('cmake --build . --config Release -j', { cwd: buildDir, stdio: 'inherit' });
                    writeFileSync(join(whisperDir, '.gpu_build'), 'cuda', 'utf8');
                } else {
                    cprint(Colors.YELLOW, '📦 Building CPU-only version...');
                    execSync('make -j', { cwd: whisperDir, stdio: 'inherit' });
                }

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
        transcribe: async (audioPath, model, language, gpuLayers = 0) => {
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
                const cpuCount = cpus().length;
                const threads = Math.min(cpuCount || 4, 8);
                const ngl = Number.isFinite(Number(gpuLayers)) ? Math.max(0, Math.floor(Number(gpuLayers))) : 0;
                const gpuBuild = existsSync(join(MODELS_DIR, 'whisper.cpp', '.gpu_build'));
                const nglArg = ngl > 0 && gpuBuild ? ` -ngl ${ngl}` : '';
                const prompt = String(process.env.STTS_STT_PROMPT || '').trim();
                const promptFlag = prompt ? detectPromptFlag(whisperBin) : null;
                const promptArg = prompt && promptFlag ? ` ${promptFlag} ${JSON.stringify(prompt)}` : '';
                const result = execSync(
                    `"${whisperBin}" -m "${modelPath}" -l ${language} -f "${audioPath}" -nt -t ${threads}${nglArg}${promptArg}`,
                    { encoding: 'utf8', timeout: 120000, stdio: ['pipe', 'pipe', 'pipe'] }
                );
                return normalizeSTTText(result.trim(), language);
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
    'spd-say': {
        name: 'spd-say',
        description: 'Speech Dispatcher (system TTS)',
        minRamGb: 0.1,
        isAvailable: () => {
            if (which('spd-say')) return [true, 'spd-say found'];
            return [false, 'install speech-dispatcher (spd-say)'];
        },
        speak: (text, voice) => {
            const cmd = which('spd-say');
            if (!cmd) return;
            try {
                spawnSync(cmd, ['-l', String(voice || 'pl'), text], { stdio: 'ignore' });
            } catch {}
        },
    },
    flite: {
        name: 'flite',
        description: 'Offline TTS (flite)',
        minRamGb: 0.1,
        isAvailable: () => {
            if (which('flite')) return [true, 'flite found'];
            return [false, 'install flite'];
        },
        speak: (text, voice) => {
            const cmd = which('flite');
            if (!cmd) return;
            try {
                const args = [];
                if (voice) args.push('-voice', String(voice));
                args.push('-t', text);
                spawnSync(cmd, args, { stdio: 'ignore' });
            } catch {}
        },
    },
    say: {
        name: 'say',
        description: 'macOS system TTS',
        minRamGb: 0.1,
        isAvailable: (info) => {
            if (info && info.osName === 'darwin' && which('say')) return [true, 'say found'];
            return [false, 'macOS only (say)'];
        },
        speak: (text, voice) => {
            const cmd = which('say');
            if (!cmd) return;
            try {
                const args = [];
                if (voice) args.push('-v', String(voice));
                args.push(text);
                spawnSync(cmd, args, { stdio: 'ignore' });
            } catch {}
        },
    },
    piper: {
        name: 'piper',
        description: 'Offline neural TTS (piper)',
        minRamGb: 0.5,
        isAvailable: () => {
            if (which('piper')) return [true, 'piper found'];
            return [false, 'install piper (binary)'];
        },
        speak: (text, voice, config) => {
            const cmd = which('piper');
            if (!cmd) return;
            const v = String(voice || '').trim();
            let modelPath = '';
            if (v) {
                if (v.endsWith('.onnx') && existsSync(v)) {
                    modelPath = v;
                } else {
                    const p = join(MODELS_DIR, 'piper', `${v}.onnx`);
                    if (existsSync(p)) modelPath = p;
                }
            }
            if (!modelPath) return;
            const outWav = join('/tmp', `stts_piper_${process.pid}_${Date.now()}.wav`);
            try {
                const res = spawnSync(cmd, ['--model', modelPath, '--output_file', outWav], {
                    input: text,
                    encoding: 'utf8',
                    stdio: ['pipe', 'ignore', 'ignore'],
                    timeout: 60000,
                });
                if (res.status !== 0) return;
                const player = which('paplay') || which('aplay') || which('play');
                if (!player) return;
                if (player.endsWith('/play')) {
                    spawnSync(player, ['-q', outWav], { stdio: 'ignore' });
                } else {
                    spawnSync(player, [outWav], { stdio: 'ignore' });
                }
            } catch {
            } finally {
                try { unlinkSync(outWav); } catch {}
            }
        },
    },
};

function recordAudio(duration = 5, outputPath = '/tmp/stts_audio.wav') {
    const info = detectSystem({ fast: true });
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
    const info = detectSystem({ fast: false });

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

    console.log(`\nTTS:`);
    const keys = Object.keys(TTS_PROVIDERS);
    const items = keys.map((k) => {
        const p = TTS_PROVIDERS[k];
        let avail = false;
        let reason = '';
        try {
            const res = p.isAvailable ? p.isAvailable(info) : [false, 'no check'];
            avail = !!res[0];
            reason = String(res[1] || '');
        } catch {
            avail = false;
            reason = 'error';
        }
        console.log(`  ${k} (${avail ? 'OK' : reason})`);
        return { key: k, avail, reason };
    });
    const ttsPick = (await question(rl, `TTS provider (ENTER=espeak): `)) || 'espeak';
    if (!TTS_PROVIDERS[ttsPick]) {
        cprint(Colors.YELLOW, `Unknown TTS provider: ${ttsPick}`);
        config.tts_provider = null;
    } else {
        const p = TTS_PROVIDERS[ttsPick];
        const res = p.isAvailable ? p.isAvailable(info) : [false, 'not available'];
        if (!res[0]) {
            cprint(Colors.YELLOW, `TTS '${ttsPick}' unavailable: ${res[1]}`);
            config.tts_provider = null;
        } else {
            config.tts_provider = ttsPick;
            const v0 = config.tts_voice || 'pl';
            config.tts_voice = (await question(rl, `TTS voice/lang (ENTER=${v0}): `)) || v0;
        }
    }

    saveConfig(config);
    cprint(Colors.GREEN, `\n✅ Konfiguracja zapisana do ${getConfigFileForSave()}`);

    rl.close();
    return config;
}

async function speak(text, config) {
    if (!config.auto_tts) return;
    const provider = config.tts_provider && TTS_PROVIDERS[config.tts_provider];
    if (!provider) return;

    const voice = config.tts_voice || 'pl';
    provider.speak(text.slice(0, 200), voice, config);
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
    const text = await provider.transcribe(audioPath, config.stt_model, config.language || 'pl', config.stt_gpu_layers || 0);

    if (text) {
        cprint(Colors.GREEN, `✅ "${text}"`);
    } else {
        cprint(Colors.RED, '❌ Nie rozpoznano');
    }

    return text;
}

async function runCommand(cmd, { stream = false } = {}) {
    if (stream) {
        return await new Promise((resolve) => {
            const argv = process.platform === 'win32' ? ['cmd', '/c', cmd] : ['bash', '-c', cmd];
            const p = spawn(argv[0], argv.slice(1), { stdio: ['inherit', 'pipe', 'pipe'] });
            let out = '';
            const onData = (buf) => {
                const s = buf.toString('utf8');
                out += s;
                process.stdout.write(s);
            };
            if (p.stdout) p.stdout.on('data', onData);
            if (p.stderr) p.stderr.on('data', onData);
            p.on('close', (code) => resolve({ output: out, code: code ?? 1, printed: true }));
            p.on('error', () => resolve({ output: '', code: 1, printed: true }));
        });
    }
    try {
        const out = execSync(cmd, {
            encoding: 'utf8',
            timeout: 60000,
            stdio: ['pipe', 'pipe', 'pipe'],
            maxBuffer: 10 * 1024 * 1024,
        });
        return { output: out, code: 0, printed: false };
    } catch (e) {
        return { output: e.stdout || e.stderr || e.message, code: e.status || 1, printed: false };
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
                const translated = await nlp2cmdTranslate(nl, { config });
                if (!translated || !nlp2cmdConfirm(translated)) {
                    prompt();
                    return;
                }
                cmd = translated;
            }

            if (!cmd) {
                nlp2cmdPrewarm(config);
                cmd = await listen(config);
                if (!cmd) {
                    prompt();
                    return;
                }
                const translated = await nlp2cmdTranslate(cmd, { config });
                if (translated && nlp2cmdConfirm(translated)) {
                    cmd = translated;
                }
            }

            cprint(Colors.BLUE, `▶️  ${cmd}`);
            const { output, code, printed } = await runCommand(cmd, { stream: !!config.stream_cmd });
            if (!printed && output.trim()) console.log(output);

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
    let streamCmd = null;
    let fastStart = null;
    let sttGpuLayers = null;
    let listTts = false;
    let ttsProvider = null;
    let ttsVoice = null;
    let nlp2cmdParallel = null;
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
        } else if (a === '--stream') {
            streamCmd = true;
        } else if (a === '--no-stream') {
            streamCmd = false;
        } else if (a === '--fast-start') {
            fastStart = true;
        } else if (a === '--full-start') {
            fastStart = false;
        } else if (a === '--stt-gpu-layers') {
            const n = Number(argv[i + 1]);
            sttGpuLayers = Number.isFinite(n) ? Math.max(0, Math.floor(n)) : 0;
            i++;
        } else if (a === '--nlp2cmd-parallel') {
            nlp2cmdParallel = true;
        } else if (a === '--no-nlp2cmd-parallel') {
            nlp2cmdParallel = false;
        } else if (a === '--list-tts') {
            listTts = true;
        } else if (a === '--tts-provider') {
            ttsProvider = argv[i + 1] || '';
            i++;
        } else if (a === '--tts-voice') {
            ttsVoice = argv[i + 1] || '';
            i++;
        } else if (a === '--help' || a === '-h') {
            help = true;
        } else {
            rest.push(a);
        }
    }

    return { sttFile, sttOnly, setup, help, streamCmd, fastStart, sttGpuLayers, listTts, ttsProvider, ttsVoice, nlp2cmdParallel, rest };
}

async function main() {
    let config = loadConfig();
    const { sttFile, sttOnly, setup, help, streamCmd, fastStart, sttGpuLayers, listTts, ttsProvider, ttsVoice, nlp2cmdParallel, rest } = parseArgs(process.argv.slice(2));

    if (streamCmd !== null) config.stream_cmd = !!streamCmd;
    if (fastStart !== null) config.fast_start = !!fastStart;
    if (sttGpuLayers !== null) config.stt_gpu_layers = Number(sttGpuLayers) || 0;
    if (ttsProvider !== null) config.tts_provider = String(ttsProvider).trim() || null;
    if (ttsVoice !== null) config.tts_voice = String(ttsVoice).trim() || config.tts_voice;
    if (nlp2cmdParallel !== null) config.nlp2cmd_parallel = !!nlp2cmdParallel;

    if (help) {
        console.log(`${readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(0, 14).join('\n')}\n`);
        console.log('Options:');
        console.log('  --setup             configure STT/TTS');
        console.log('  --stt-file PATH     use WAV file instead of recording');
        console.log('  --stt-only          only transcribe (do not execute)');
        console.log('  --stream/--no-stream  stream command output (no buffering)');
        console.log('  --fast-start/--full-start  faster startup / full detection');
        console.log('  --stt-gpu-layers N   whisper.cpp: offload N layers to GPU (-ngl)');
        console.log('  --nlp2cmd-parallel/--no-nlp2cmd-parallel  prewarm nlp2cmd worker');
        console.log('  --tts-provider NAME  set TTS provider (espeak/piper/spd-say/flite/say)');
        console.log('  --tts-voice VALUE    set TTS voice/lang');
        console.log('  --list-tts           list available TTS providers');
        return;
    }

    if (listTts) {
        const info = detectSystem({ fast: true });
        for (const k of Object.keys(TTS_PROVIDERS).sort()) {
            const p = TTS_PROVIDERS[k];
            let ok = false;
            let reason = '';
            try {
                const r = p.isAvailable ? p.isAvailable(info) : [false, 'no check'];
                ok = !!r[0];
                reason = String(r[1] || '');
            } catch {
                ok = false;
                reason = 'error';
            }
            console.log(`${k}: ${ok ? 'ok' : 'no'} (${reason})`);
        }
        return;
    }

    if (setup || (!config.stt_provider && !config.tts_provider && !sttFile && rest.length === 0)) {
        config = await interactiveSetup();
    }

    if (ttsProvider !== null || ttsVoice !== null || streamCmd !== null || fastStart !== null || nlp2cmdParallel !== null) {
        saveConfig(config);
    }

    if (sttFile) {
        nlp2cmdPrewarm(config);
        const shellText = await listen(config, sttFile);
        if (sttOnly) {
            console.log(shellText);
            process.exit(shellText ? 0 : 1);
        }
        if (!shellText) process.exit(1);
        let cmd = shellText;
        const translated = await nlp2cmdTranslate(cmd, { config });
        if (translated && nlp2cmdConfirm(translated)) cmd = translated;
        const { output, code, printed } = await runCommand(cmd, { stream: !!config.stream_cmd });
        if (!printed && output.trim()) console.log(output);
        process.exit(code);
    }

    if (rest.length === 0) {
        await voiceShell(config);
        return;
    }

    if (nlp2cmdParallelEnabled(config)) {
        const bin = process.env.STTS_NLP2CMD_BIN || 'nlp2cmd';
        if (rest[0] === bin && rest.some((a) => String(a || '').includes('{STT}'))) {
            const runMode = rest.includes('-r') || rest.includes('--run');
            const autoConfirm = rest.includes('--auto-confirm');

            nlp2cmdPrewarm(config);
            const shellText = await listen(config);
            if (!shellText) process.exit(1);

            const translated = await nlp2cmdTranslate(shellText, { config, force: true });
            if (!translated) process.exit(1);

            if (!autoConfirm) {
                if (!nlp2cmdConfirm(translated)) process.exit(0);
            }

            if (!runMode) {
                console.log(translated);
                process.exit(0);
            }

            const { output, code, printed } = await runCommand(translated, { stream: !!config.stream_cmd });
            if (!printed && output.trim()) console.log(output);
            process.exit(code);
        }
    }

    const cmd = rest.join(' ');
    const { output, code, printed } = await runCommand(cmd, { stream: !!config.stream_cmd });
    if (!printed && output.trim()) console.log(output);

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
