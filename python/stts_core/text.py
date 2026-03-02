"""Text normalization for STT (Speech-to-Text) corrections.

This module provides the TextNormalizer class which corrects common STT errors,
especially for technical terms and shell commands in Polish and English.
"""

import difflib
import functools
import re
from typing import Optional


class TextNormalizer:
    """Normalizuje i koryguje tekst z STT dla poleceń shell."""

    SHELL_CORRECTIONS = {
        "el es": "ls",
        "el s": "ls",
        "lista": "ls",
        "l s": "ls",
        "kopi": "cp",
        "kopiuj": "cp",
        "przenieś": "mv",
        "usuń": "rm",
        "katalog": "mkdir",
        "pokaż": "cat",
        "edytuj": "nano",
        "eko": "echo",
        "cd..": "cd ..",
        "cd -": "cd -",
        "git status": "git status",
        "git commit": "git commit",
        "git pusz": "git push",
        "git pul": "git pull",
        "pip instal": "pip install",
        "sudo apt instal": "sudo apt install",
    }

    PHONETIC_EN_CORRECTIONS = {
        "serwer": "server",
        "servera": "server",
        "serwera": "server",
        "serwerze": "server",
        "serwery": "servers",
        "endżineks": "nginx",
        "endżinks": "nginx",
        "enginx": "nginx",
        "engines": "nginx",
        "endżin": "engine",
        "endżiny": "engines",
        "dokker": "docker",
        "doker": "docker",
        "dockera": "docker",
        "dokera": "docker",
        "kubernetis": "kubernetes",
        "kubernitis": "kubernetes",
        "kej eight": "k8s",
        "kej ejtis": "k8s",
        "kej ejts": "k8s",
        "kej8s": "k8s",
        "kubektl": "kubectl",
        "kubkontrol": "kubectl",
        "kubctl": "kubectl",
        "postgresem": "postgres",
        "postgresom": "postgres",
        "postgresa": "postgres",
        "postgressa": "postgres",
        "eskuel": "sql",
        "es kju el": "sql",
        "eskjuel": "sql",
        "majeskuel": "mysql",
        "majsql": "mysql",
        "mysquel": "mysql",
        "mongo di bi": "mongodb",
        "mongodi": "mongodb",
        "mongołdi": "mongodb",
        "redisa": "redis",
        "redys": "redis",
        "elastik": "elastic",
        "elasticsearch": "elasticsearch",
        "elastiksercz": "elasticsearch",
        "apacz": "apache",
        "apatche": "apache",
        "apacze": "apache",
        "nodżejejs": "nodejs",
        "noddżejs": "nodejs",
        "nodżs": "nodejs",
        "node dżejs": "nodejs",
        "nodjs": "nodejs",
        "piton": "python",
        "pajton": "python",
        "pajtona": "python",
        "pytona": "python",
        "dżawa": "java",
        "dżawy": "java",
        "dżawą": "java",
        "dżawaskrypt": "javascript",
        "jawa skrypt": "javascript",
        "dżejs": "js",
        "jst": "js",
        "tajpskrypt": "typescript",
        "tajp skrypt": "typescript",
        "reakt": "react",
        "reakta": "react",
        "wju": "vue",
        "wjuejs": "vuejs",
        "angulara": "angular",
        "angularem": "angular",
        "netflajs": "nextjs",
        "nekst dżejs": "nextjs",
        "nestjs": "nestjs",
        "ekspres": "express",
        "ekspresa": "express",
        "flaskem": "flask",
        "dżango": "django",
        "dżanga": "django",
        "laravel": "laravel",
        "larawel": "laravel",
        "symfonią": "symfony",
        "springa": "spring",
        "springbutem": "springboot",
        "majkroserwisy": "microservices",
        "majkroservisy": "microservices",
        "mikroserwisy": "microservices",
        "rest ejpi aj": "rest api",
        "rest api": "rest api",
        "restejpiaj": "rest api",
        "dżejson": "json",
        "jsoń": "json",
        "jaml": "yaml",
        "jamł": "yaml",
        "tomł": "toml",
        "toml": "toml",
        "iniajalizuj": "initialize",
        "initializuj": "initialize",
        "inital": "init",
        "inituj": "init",
        "deploj": "deploy",
        "deplojuj": "deploy",
        "deplojem": "deploy",
        "deploymenta": "deployment",
        "deploimentu": "deployment",
        "bilda": "build",
        "bildem": "build",
        "bilduj": "build",
        "starta": "start",
        "startuj": "start",
        "restarta": "restart",
        "restartuj": "restart",
        "stopa": "stop",
        "stopuj": "stop",
        "testa": "test",
        "testuj": "test",
        "lintuj": "lint",
        "lintera": "linter",
        "awsa": "aws",
        "awsie": "aws",
        "ejdablju es": "aws",
        "azura": "azure",
        "ejżur": "azure",
        "dżi si pi": "gcp",
        "google cloud": "gcp",
        "heroku": "heroku",
        "netlify": "netlify",
        "wercel": "vercel",
        "wersela": "vercel",
        "terraforma": "terraform",
        "teraform": "terraform",
        "ansibla": "ansible",
        "ansiblem": "ansible",
        "dżenkinsem": "jenkins",
        "dżenkinsa": "jenkins",
        "jenkinsa": "jenkins",
        "siajaidi": "ci/cd",
        "ci cd": "ci/cd",
        "si aj si di": "ci/cd",
        "githuba": "github",
        "gitlaba": "gitlab",
        "gitłab": "gitlab",
        "bitketa": "bitbucket",
        "bitbaketa": "bitbucket",
        "prullrikłest": "pull request",
        "pul rekłest": "pull request",
        "pul rikłest": "pull request",
        "merdż": "merge",
        "merdżuj": "merge",
        "brenczem": "branch",
        "brancz": "branch",
        "brencza": "branch",
        "komitta": "commit",
        "komituj": "commit",
        "komitem": "commit",
        "kontejnera": "container",
        "kontejner": "container",
        "kontener": "container",
        "kontenera": "container",
        "imidża": "image",
        "imidż": "image",
        "imidżem": "image",
        "wolumena": "volume",
        "wolumen": "volume",
        "networkiem": "network",
        "sieć": "network",
        "sieci": "network",
        "serwisem": "service",
        "serwisy": "services",
        "serwis": "service",
        "podów": "pods",
        "pody": "pods",
        "podem": "pod",
        "namespacie": "namespace",
        "nejmspejs": "namespace",
        "helma": "helm",
        "helmem": "helm",
        "istio": "istio",
        "prometheusa": "prometheus",
        "prometeus": "prometheus",
        "grafaną": "grafana",
        "grafana": "grafana",
        "kibaną": "kibana",
        "kibana": "kibana",
        "logstashem": "logstash",
        "logstasz": "logstash",
        "rabbitmq": "rabbitmq",
        "rabit em kju": "rabbitmq",
        "kafką": "kafka",
        "kafki": "kafka",
        "kafkem": "kafka",
        "celery": "celery",
        "selerym": "celery",
    }

    REGEX_FIXES = [
        (r"\bel\s+es\b", "ls"),
        (r"\bel\s+s\b", "ls"),
        (r"\bl\s+s\b", "ls"),
        (r"\bgit\s+stat\b", "git status"),
        (r"\bgit\s+pusz\b", "git push"),
        (r"\bgit\s+pul\b", "git pull"),
        (r"\bgrepp?\b", "grep"),
        (r"\bsudo\s+apt\s+instal\b", "sudo apt install"),
        (r"\bpip\s+instal\b", "pip install"),
        (r"\beko\s+", "echo "),
        (r"\bkopi\s+", "cp "),
        (r"\bmkdir\s+-p\s*", "mkdir -p "),
        (r"\bservera?\s+engines?\b", "nginx server"),
        (r"\bserwera?\s+engines?\b", "nginx server"),
        (r"\bserwer\s+endżi?n?e?ks?\b", "nginx server"),
        (r"\bdocker\s+kompo[uz]e?\b", "docker compose"),
        (r"\bdocker\s+kompoza?\b", "docker compose"),
        (r"\bdokker\s+kompo[uz]e?\b", "docker compose"),
        (r"\bkube?r?netis\b", "kubernetes"),
        (r"\bkube?rnitis\b", "kubernetes"),
    ]

    @classmethod
    def normalize(cls, text: str, language: str = "pl") -> str:
        """Normalizuje tekst STT - usuwa błędy, poprawia komendy."""
        if not text:
            return ""

        result = text.strip()

        result = re.sub(r"[.,!?;:]+$", "", result)

        for pattern, replacement in cls.REGEX_FIXES:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        result = cls._fix_phonetic_english(result, language)

        lower = result.lower().strip()
        for wrong, correct in cls.SHELL_CORRECTIONS.items():
            if lower == wrong:
                return correct

        return result

    @classmethod
    def _fix_phonetic_english(cls, text: str, language: str = "pl") -> str:
        """Poprawia angielskie słowa techniczne zapisane fonetycznie po polsku."""
        if (language or "pl").lower() not in ("pl", "polish"):
            return text

        words = text.split()
        fixed = []
        for word in words:
            m = re.match(r"^([.,!?;:\"\'()\[\]{}]*)(.*?)([.,!?;:\"\'()\[\]{}]*)$", word)
            if not m:
                fixed.append(word)
                continue
            prefix, core, suffix = m.groups()
            if not core:
                fixed.append(word)
                continue

            clean = core.lower()
            replacement = cls.PHONETIC_EN_CORRECTIONS.get(clean)
            if replacement is None:
                replacement = cls._fuzzy_phonetic_replacement(clean)
            if replacement is None:
                fixed.append(word)
                continue

            if core[:1].isupper() and replacement[:1].isalpha():
                replacement = replacement[:1].upper() + replacement[1:]
            fixed.append(f"{prefix}{replacement}{suffix}")
        return " ".join(fixed)

    @staticmethod
    @functools.lru_cache(maxsize=4096)
    def _fuzzy_phonetic_replacement(clean: str) -> Optional[str]:
        s = (clean or "").strip().lower()
        if not s:
            return None
        if len(s) < 4 or len(s) > 18:
            return None
        if not s.isalpha():
            return None

        keys = [k for k in TextNormalizer.PHONETIC_EN_CORRECTIONS.keys() if " " not in k]
        candidates = [k for k in keys if abs(len(k) - len(s)) <= 2]
        if not candidates:
            return None

        try:
            from rapidfuzz import fuzz as _rf_fuzz  # type: ignore
            from rapidfuzz import process as _rf_process  # type: ignore

            hit = _rf_process.extractOne(s, candidates, scorer=_rf_fuzz.ratio, score_cutoff=84)
            if not hit:
                return None
            return TextNormalizer.PHONETIC_EN_CORRECTIONS.get(hit[0])
        except Exception:
            pass

        m = difflib.get_close_matches(s, candidates, n=1, cutoff=0.84)
        if not m:
            return None
        return TextNormalizer.PHONETIC_EN_CORRECTIONS.get(m[0])


def normalize_stt(text: str, language: str = "pl", context: str = "command") -> str:
    """Convenience function to normalize STT text.
    
    Args:
        text: Raw STT text to normalize
        language: Language code (default: "pl")
        context: Context for normalization ("command", "dictation", or "nlp2cmd")
        
    Returns:
        Normalized text
    """
    return TextNormalizer.normalize(text, language)
