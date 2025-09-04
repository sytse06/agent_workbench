#!/bin/bash

# scripts/scope/agent_scope_check.sh
# Human-Steered AI Development - Generic ADR-Driven Scope Compliance
# Parses ADR files and generates AI prompts for thorough scope compliance checking

set -e

TASK_ID=${1:-""}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs/architecture/decisions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_section() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

# Parse ADR file to extract scope boundaries
parse_adr() {
    local adr_file="$1"
    
    if [[ ! -f "$adr_file" ]]; then
        log_fail "ADR file not found: $adr_file"
        return 1
    fi
    
    log_info "Parsing ADR: $(basename "$adr_file")"
    
    # Extract sections using markdown parsing
    AWK_SCRIPT='
    BEGIN { 
        in_included = 0
        in_excluded = 0
        in_boundaries = 0
        in_forbidden = 0
        in_signatures = 0
        in_dependencies = 0
    }
    
    # Track sections
    /### What.s Included:/ { in_included = 1; next }
    /### What.s Explicitly Excluded:/ { in_included = 0; in_excluded = 1; next }
    /### Implementation Boundaries/ { in_excluded = 0; in_boundaries = 1; next }
    /### Files to CREATE:/ { in_boundaries = 1; next }
    /### FORBIDDEN Actions:/ { in_boundaries = 0; in_forbidden = 1; next }
    /### Exact Function Signatures:/ { in_forbidden = 0; in_signatures = 1; next }
    /### Required Dependencies:/ { in_signatures = 0; in_dependencies = 1; next }
    
    # Reset on new major section
    /^## / { in_included = 0; in_excluded = 0; in_boundaries = 0; in_forbidden = 0; in_signatures = 0; in_dependencies = 0 }
    
    # Extract content
    in_included && /^- \[.\] / { gsub(/^- \[.\] /, ""); print "INCLUDED:" $0 }
    in_excluded && /^- / { gsub(/^- /, ""); print "EXCLUDED:" $0 }
    in_boundaries && /CREATE:/ { print "CREATE_FILES:" $0 }
    in_boundaries && /MODIFY:/ { print "MODIFY_FILES:" $0 }
    in_forbidden && /^- / { gsub(/^- /, ""); print "FORBIDDEN:" $0 }
    in_signatures && /async def / { print "SIGNATURE:" $0 }
    in_dependencies && /".*"/ { print "DEPENDENCY:" $0 }
    '
    
    awk "$AWK_SCRIPT" "$adr_file" > /tmp/adr_parsed_$$
}

# Generate AI compliance prompt from parsed ADR
generate_ai_prompt() {
    local parsed_file="/tmp/adr_parsed_$$"
    local task_id="$1"
    
    cat > /tmp/ai_scope_prompt_$$ << EOF
# SCOPE COMPLIANCE VERIFICATION PROMPT
# Task: $task_id
# Generated: $(date)
# Human-Steered AI Development - Boundary Enforcement

## YOUR ROLE
You are a **Scope Compliance Auditor** for human-steered AI development. Your job is to verify that implementation stays within the exact boundaries defined in the architectural decision record (ADR).

## CRITICAL INSTRUCTIONS
- Check EVERY item listed below against the actual implementation
- Report violations as SCOPE VIOLATIONS with severity level
- Be thorough and precise - scope boundaries are sacred
- If uncertain, flag as potential violation for human review

## SCOPE BOUNDARIES TO VERIFY

### ✅ REQUIRED INCLUSIONS (Must be implemented)
EOF
    
    # Add included items
    grep "^INCLUDED:" "$parsed_file" 2>/dev/null | sed 's/^INCLUDED:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No specific inclusions defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

### ❌ EXPLICIT EXCLUSIONS (Must NOT be implemented)
EOF
    
    # Add excluded items
    grep "^EXCLUDED:" "$parsed_file" 2>/dev/null | sed 's/^EXCLUDED:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No specific exclusions defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

### 📁 FILE CREATION BOUNDARIES
EOF
    
    # Add file boundaries
    grep "^CREATE_FILES:" "$parsed_file" 2>/dev/null | sed 's/^CREATE_FILES:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No file creation boundaries defined)" >> /tmp/ai_scope_prompt_$$
    grep "^MODIFY_FILES:" "$parsed_file" 2>/dev/null | sed 's/^MODIFY_FILES:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No file modification boundaries defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

### 🚫 FORBIDDEN ACTIONS
EOF
    
    # Add forbidden actions
    grep "^FORBIDDEN:" "$parsed_file" 2>/dev/null | sed 's/^FORBIDDEN:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No forbidden actions defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

### 📋 REQUIRED FUNCTION SIGNATURES
EOF
    
    # Add signatures
    grep "^SIGNATURE:" "$parsed_file" 2>/dev/null | sed 's/^SIGNATURE:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No specific function signatures defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

### 📦 DEPENDENCY CONSTRAINTS  
EOF
    
    # Add dependencies
    grep "^DEPENDENCY:" "$parsed_file" 2>/dev/null | sed 's/^DEPENDENCY:/- /' >> /tmp/ai_scope_prompt_$$ || echo "- (No dependency constraints defined)" >> /tmp/ai_scope_prompt_$$
    
    cat >> /tmp/ai_scope_prompt_$$ << EOF

## VERIFICATION CHECKLIST

### 1. INCLUSION COMPLIANCE
For each required inclusion above:
- [ ] Verify it exists in the codebase
- [ ] Check it meets the specified requirements
- [ ] Report any missing implementations as VIOLATIONS

### 2. EXCLUSION COMPLIANCE  
For each explicit exclusion above:
- [ ] Verify it does NOT exist in the codebase
- [ ] Check for indirect implementations (imports, references)
- [ ] Report any violations as SCOPE CREEP

### 3. FILE BOUNDARY COMPLIANCE
- [ ] Verify only specified files were created/modified
- [ ] Check no unauthorized files were added
- [ ] Validate file structure matches ADR specifications

### 4. CODE PATTERN COMPLIANCE
- [ ] Verify all function signatures match ADR specifications
- [ ] Check for forbidden imports or patterns
- [ ] Validate architectural patterns are followed

### 5. DEPENDENCY COMPLIANCE
- [ ] Verify only required dependencies were added
- [ ] Check no forbidden dependencies were introduced
- [ ] Validate dependency versions and configurations

## REPORTING FORMAT

For each check, report using this format:

\`\`\`
CHECK: [Description]
STATUS: ✅ COMPLIANT | ❌ VIOLATION | ⚠️ WARNING
DETAILS: [Specific findings]
SEVERITY: LOW | MEDIUM | HIGH | CRITICAL
RECOMMENDATION: [What should be done]
\`\`\`

## FINAL ASSESSMENT

After all checks, provide:

1. **SCOPE COMPLIANCE SCORE**: X/Y checks passed
2. **VIOLATION SUMMARY**: List all violations by severity
3. **RECOMMENDATION**: APPROVE | CONDITIONAL APPROVE | REJECT
4. **HUMAN REVIEW ITEMS**: Issues requiring human judgment

Remember: The human architect set these boundaries for good reasons. Your job is to enforce them rigorously to maintain architectural integrity and prevent scope creep.

---

**Now perform the scope compliance verification on the current codebase for task $task_id.**
EOF
    
    echo "/tmp/ai_scope_prompt_$$"
}

# Execute AI audit using Ollama
execute_ai_audit() {
    local prompt_file="$1"
    local task_id="$2"
    
    log_section "AI SCOPE AUDIT EXECUTION"
    
    # Check for Ollama and mistral model
    if ! command -v ollama >/dev/null 2>&1; then
        log_warn "Ollama not found - install from https://ollama.com/"
        return 1
    fi
    
    # Show available models
    echo -e "${BLUE}Available Ollama models:${NC}"
    ollama list | head -5
    echo ""
    
    # Check if mistral model is available
    if ! ollama list | grep -q "mistral"; then
        log_warn "Mistral model not found. Installing..."
        echo "This may take a few minutes..."
        if ollama pull mistral; then
            log_pass "Mistral model installed successfully"
        else
            log_fail "Failed to install Mistral model"
            return 1
        fi
    else
        log_pass "Mistral model found"
    fi
    
    echo ""
    log_info "Executing AI audit via Ollama Mistral..."
    echo -e "${YELLOW}Sending prompt to Mistral (this may take 30-60 seconds)...${NC}"
    echo ""
    
    # Show the prompt being sent
    echo -e "${CYAN}--- PROMPT BEING SENT TO MISTRAL ---${NC}"
    echo "$(head -20 "$prompt_file")..."
    echo -e "${CYAN}--- END PROMPT PREVIEW ---${NC}"
    echo ""
    
    # Create audit header
    echo "=== AI SCOPE COMPLIANCE AUDIT ===" | tee /tmp/audit_result_$
    echo "Task: $task_id" | tee -a /tmp/audit_result_$
    echo "Audit Date: $(date)" | tee -a /tmp/audit_result_$
    echo "Model: Mistral via Ollama" | tee -a /tmp/audit_result_$
    echo "" | tee -a /tmp/audit_result_$
    
    echo -e "${PURPLE}🤖 AI AUDIT IN PROGRESS - STREAMING RESPONSE:${NC}"
    echo -e "${PURPLE}================================================${NC}"
    
    # Run the audit with live streaming output
    if ollama run mistral < "$prompt_file" | tee -a /tmp/audit_result_$; then
        echo ""
        echo -e "${PURPLE}================================================${NC}"
        log_pass "AI audit completed successfully"
        return 0
    else
        echo ""
        log_fail "Ollama audit execution failed"
        echo "Checking for error details..."
        if [[ -f /tmp/audit_result_$ ]]; then
            echo "Last few lines of output:"
            tail -10 /tmp/audit_result_$
        fi
        return 1
    fi
}

# Run automated checks that can be verified programmatically
run_automated_checks() {
    local adr_file="$1"
    local parsed_file="/tmp/adr_parsed_$$"
    
    log_section "AUTOMATED SCOPE CHECKS"
    
    # Show what forbidden actions were defined
    echo ""
    echo -e "${BLUE}📋 Forbidden actions from ADR:${NC}"
    if grep -q "^FORBIDDEN:" "$parsed_file" 2>/dev/null; then
        grep "^FORBIDDEN:" "$parsed_file" | sed 's/^FORBIDDEN:/   - /'
    else
        echo "   - (No forbidden actions defined)"
    fi
    echo ""
    
    # Check file existence from CREATE/MODIFY directives
    while IFS=: read -r type files_line; do
        if [[ "$type" == "CREATE_FILES" || "$type" == "MODIFY_FILES" ]]; then
            # Extract file paths from the line
            echo "$files_line" | grep -o '`[^`]*`' | sed 's/`//g' | while read -r file_path; do
                if [[ -n "$file_path" && "$file_path" == *"src/"* ]]; then
                    full_path="$PROJECT_ROOT/$file_path"
                    if [[ -f "$full_path" ]]; then
                        log_pass "Required file exists: $file_path"
                    else
                        log_fail "Required file missing: $file_path"
                    fi
                fi
            done
        fi
    done < "$parsed_file" 2>/dev/null
    
    # Check for forbidden patterns
    local src_dir="$PROJECT_ROOT/src"
    if [[ -d "$src_dir" ]]; then
        # Extract forbidden patterns from ADR and look for violations
        while IFS=: read -r type content; do
            if [[ "$type" == "FORBIDDEN" ]]; then
                # Look for LLM-related violations
                if echo "$content" | grep -q -i "llm\|openai\|anthropic"; then
                    echo -e "${BLUE}🔍 Checking for forbidden LLM imports...${NC}"
                    if grep -r -n "^import.*\(openai\|anthropic\|langchain\)\|^from.*\(openai\|anthropic\|langchain\)" "$src_dir" 2>/dev/null; then
                        log_fail "Found forbidden LLM imports (scope violation)"
                        echo "   Violations found:"
                        grep -r -n "^import.*\(openai\|anthropic\|langchain\)\|^from.*\(openai\|anthropic\|langchain\)" "$src_dir" 2>/dev/null | sed 's/^/      /'
                    else
                        log_pass "No forbidden LLM imports detected"
                    fi
                fi
                
                # Look for UI-related violations
                if echo "$content" | grep -q -i "ui\|gradio"; then
                    echo -e "${BLUE}🔍 Checking for forbidden UI imports...${NC}"
                    if grep -r -n "^import.*gradio\|^from.*gradio" "$src_dir" 2>/dev/null; then
                        log_fail "Found forbidden UI imports (scope violation)"
                        echo "   Violations found:"
                        grep -r -n "^import.*gradio\|^from.*gradio" "$src_dir" 2>/dev/null | sed 's/^/      /'
                    else
                        log_pass "No forbidden UI imports detected"
                    fi
                fi
            fi
        done < "$parsed_file" 2>/dev/null
    fi
    
    # Check dependencies
    local pyproject_file="$PROJECT_ROOT/pyproject.toml"
    if [[ -f "$pyproject_file" ]]; then
        echo -e "${BLUE}🔍 Checking dependency compliance...${NC}"
        while IFS=: read -r type dep; do
            if [[ "$type" == "DEPENDENCY" ]]; then
                dep_name=$(echo "$dep" | grep -o '"[^"]*"' | head -1 | tr -d '"')
                if [[ -n "$dep_name" ]]; then
                    if grep -q "\"$dep_name" "$pyproject_file"; then
                        log_pass "Required dependency present: $dep_name"
                    else
                        log_warn "Required dependency not found: $dep_name"
                    fi
                fi
            fi
        done < "$parsed_file" 2>/dev/null
    fi
}

# Main function
main() {
    log_section "HUMAN-STEERED AI DEVELOPMENT"
    echo "Agent Scope Compliance Check"
    echo "Task: ${TASK_ID}"
    echo "Date: $(date)"
    echo ""
    
    # Find ADR file
    local adr_file=""
    if [[ -f "$DOCS_DIR/${TASK_ID}.md" ]]; then
        adr_file="$DOCS_DIR/${TASK_ID}.md"
    elif [[ -f "$DOCS_DIR/${TASK_ID,,}.md" ]]; then
        adr_file="$DOCS_DIR/${TASK_ID,,}.md"
    else
        # Try to find by partial match
        adr_file=$(find "$DOCS_DIR" -name "*$(echo $TASK_ID | cut -d- -f1-2)*" -type f | head -1)
    fi
    
    if [[ -z "$adr_file" || ! -f "$adr_file" ]]; then
        log_fail "Could not find ADR file for task: $TASK_ID"
        echo "Looked in: $DOCS_DIR"
        echo "Expected: ${TASK_ID}.md or similar"
        exit 1
    fi
    
    log_info "Found ADR: $(basename "$adr_file")"
    
    # Parse ADR and generate checks
    parse_adr "$adr_file"
    local prompt_file=$(generate_ai_prompt "$TASK_ID")
    
    # Run automated checks
    run_automated_checks "$adr_file"
    
    # Execute AI audit
    execute_ai_audit "$prompt_file" "$TASK_ID"
    local ai_audit_result=$?
    
    # Summary
    log_section "COMPREHENSIVE COMPLIANCE SUMMARY"
    echo -e "Automated Checks - Passed: ${GREEN}$PASS_COUNT${NC} | Failed: ${RED}$FAIL_COUNT${NC} | Warnings: ${YELLOW}$WARN_COUNT${NC}"
    
    if [[ $ai_audit_result -eq 0 ]]; then
        echo -e "AI Audit: ${GREEN}✅ Completed${NC}"
    else
        echo -e "AI Audit: ${YELLOW}⚠️ Failed or unavailable${NC}"
        echo ""
        echo -e "${BLUE}📋 Manual AI Review Required:${NC}"
        echo "Copy the prompt below and run it through your preferred AI:"
        echo ""
        echo -e "${CYAN}========== AI SCOPE AUDIT PROMPT ==========${NC}"
        cat "$prompt_file"
        echo -e "${CYAN}===========================================${NC}"
    fi
    
    echo ""
    
    # Final assessment
    if [[ $FAIL_COUNT -eq 0 ]]; then
        if [[ $ai_audit_result -eq 0 ]]; then
            echo -e "${GREEN}✅ COMPREHENSIVE SCOPE COMPLIANCE: APPROVED${NC}"
            echo "Both automated checks and AI audit passed successfully."
        else
            echo -e "${YELLOW}⚠️ SCOPE COMPLIANCE: AUTOMATED CHECKS PASSED${NC}"
            echo "Manual AI audit required for complete verification."
        fi
        exit 0
    else
        echo -e "${RED}❌ SCOPE COMPLIANCE: VIOLATIONS DETECTED${NC}"
        echo "Fix automated check failures before proceeding."
        exit 1
    fi
}

# Show usage if no arguments
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <TASK-ID>"
    echo ""
    echo "Examples:"
    echo "  $0 CORE-002-database-models-api-foundation"
    echo "  $0 LLM-001-langchain-model-integration"
    echo "  $0 UI-001-gradio-frontend-integration"
    echo ""
    echo "This script:"
    echo "1. Parses the ADR file for the specified task"
    echo "2. Runs automated scope compliance checks"
    echo "3. Executes AI-powered scope audit via Ollama Mistral"
    echo ""
    echo "Requirements:"
    echo "- Ollama installed (https://ollama.com/)"
    echo "- Mistral model (auto-installed if missing)"
    echo "- ADR files in: docs/architecture/decisions/"
    exit 1
fi

main "$@"

# Cleanup on exit
trap 'rm -f /tmp/adr_parsed_$$ /tmp/ai_scope_prompt_$$ /tmp/audit_result_$$' EXIT