#!/usr/bin/env python3
import sys
import re

def disable_debug_prints(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Regex para encontrar linhas com print(f"DEBUG:
    pattern = r'(\s+)(print\(f"DEBUG:.+)'
    
    # Substituir por versão comentada
    modified = re.sub(pattern, r'\1# \2', content, flags=re.MULTILINE)
    
    with open(filename, 'w') as f:
        f.write(modified)
    
    # Contar substituições
    original_count = len(re.findall(r'print\(f"DEBUG:', content, re.MULTILINE))
    final_count = len(re.findall(r'print\(f"DEBUG:', modified, re.MULTILINE))
    commented_count = original_count - final_count
    
    print(f"Comentadas {commented_count} linhas de debug em {filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python disable_debug.py <arquivo>")
        sys.exit(1)
    
    disable_debug_prints(sys.argv[1])
