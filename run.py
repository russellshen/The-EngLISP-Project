# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.
#
# For commercial licensing inquiries, please contact:
# Russell Shen (russellshen7@gmail.com)
#
# Licensing terms, scope, and compensation are subject to separate negotiation.
#
# Reference the footer section of any of the 4 .md files (README.md, SPECIFICATION.md,
# USE_CASES.md, LEXICAL_STRATEGIES.md) in the project's root directory for full licensing details.
#
# I am the sole original creator of the EngLISP project (around August 2025), and did not rely on
# the resources of any academic institution or private individual to develop it.

import uvicorn
import sys

def main():
    print("==================================================================")
    print("                    EngLISP Bridge Engine                         ")
    print("  Bidirectional Natural Language & Computation Interface Dashboard ")
    print("==================================================================")
    print("\nStarting the server... Open your browser to:")
    print("--> http://127.0.0.1:8000\n")
    
    try:
        uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nServer stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
