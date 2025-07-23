#!/usr/bin/env python3
"""
Script to fix formatting issues in the high conviction detector
"""

def fix_formatting_issues():
    """Fix all formatting issues in the detector"""
    
    file_path = "scripts/high_conviction_token_detector.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define replacements to fix table formatting
    replacements = [
        # Fix table output - replace line-by-line with complete table output
        (
            '                    # Print table line by line for logger compatibility\n'
            '                    table_lines = str(table).split(\'\\n\')\n'
            '                    for line in table_lines:\n'
            '                        self.logger.info(f"    {line}")',
            '                    # Print complete table as single string\n'
            '                    self.logger.info(f"\\n{table}")'
        ),
        
        # Fix session token summary table formatting
        (
            '            # Print overview table\n'
            '            table_lines = str(overview_table).split(\'\\n\')\n'
            '            for line in table_lines:\n'
            '                self.logger.info(f"  {line}")',
            '            # Print overview table\n'
            '            self.logger.info(f"\\n{overview_table}")'
        ),
        
        # Fix score table formatting
        (
            '            # Print score table\n'
            '            table_lines = str(score_table).split(\'\\n\')\n'
            '            for line in table_lines:\n'
            '                self.logger.info(f"  {line}")',
            '            # Print score table\n'
            '            self.logger.info(f"\\n{score_table}")'
        ),
        
        # Fix high conviction table formatting
        (
            '                # Print high conviction table\n'
            '                table_lines = str(hc_table).split(\'\\n\')\n'
            '                for line in table_lines:\n'
            '                    self.logger.info(f"  {line}")',
            '                # Print high conviction table\n'
            '                self.logger.info(f"\\n{hc_table}")'
        ),
        
        # Fix cross-platform table formatting
        (
            '                # Print cross-platform table\n'
            '                table_lines = str(cp_table).split(\'\\n\')\n'
            '                for line in table_lines:\n'
            '                    self.logger.info(f"  {line}")',
            '                # Print cross-platform table\n'
            '                self.logger.info(f"\\n{cp_table}")'
        ),
        
        # Fix progression table formatting
        (
            '                # Print progression table\n'
            '                table_lines = str(prog_table).split(\'\\n\')\n'
            '                for line in table_lines:\n'
            '                    self.logger.info(f"  {line}")',
            '                # Print progression table\n'
            '                self.logger.info(f"\\n{prog_table}")'
        ),
        
        # Remove excessive spacing and clean up borders
        ('================================================================================', '=' * 60),
        ('------------------------------------------------------------', '-' * 60),
        
        # Clean up excessive newlines
        ('\n\n\n', '\n\n'),
        
        # Fix debug mode check to reduce verbosity
        ('if self.debug_mode:', 'if False:  # Disable debug output'),
    ]
    
    # Apply replacements
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✅ Fixed: {old[:50]}...")
    
    if modified:
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated {file_path} with clean formatting")
    else:
        print("ℹ️  No formatting issues found to fix")

if __name__ == "__main__":
    fix_formatting_issues() 