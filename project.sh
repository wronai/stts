#!/usr/bin/env bash
code2logic ./nodejs -f toon --compact --function-logic --with-schema -o nodejs.toon
code2logic ./python -f toon --compact --function-logic --with-schema -o python.toon
