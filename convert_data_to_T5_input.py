import sys
import re

state_pattern = re.compile(r"^_STATE_ (.*)$")
action_pattern = re.compile(r"^_ACTION_ (.*)$")


def main():
    
    args = sys.argv
    if len(args) < 2: print("argv needs data file path."); return
    
    data_file = args[1].strip()

    f =  open(data_file, 'r', encoding = 'utf-8')
    if f == None: print("Failed to open data file."); return
    
    fout_ids = open('t5_input_ids.txt', 'a', encoding = 'utf-8')
    if fout_ids == None: print("Failed to open file t5_input_ids.txt."); return
    
    fout_lbs = open('t5_labels.txt', 'a', encoding = 'utf-8')
    if fout_lbs == None: print("Failed to open file t5_labels.txt."); return

    
    for line in f:
        print(line)
        state_line = state_pattern.match(line)
        action_line = action_pattern.match(line)
        if state_line:
            print("state_line match")
            fout_ids.write(state_line.group(1)+'\n')
        if action_line:
            print("action_line match")
            fout_lbs.write(action_line.group(1)+'\n')
            
    f.close()
    fout_ids.close()
    fout_lbs.close()

if __name__ == '__main__':
    main()
