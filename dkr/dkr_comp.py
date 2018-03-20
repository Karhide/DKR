import yaml
import os
import sys



def run_main(args=sys.argv[1:]):
    try:
        prefix=sys.argv[1]
    except:
        prefix=""
    
    HOME = os.path.expanduser('~')
    CONFIG_FILE = os.path.join(HOME, '.dkr')
    
    with open(CONFIG_FILE) as c:
        cfg = yaml.load(c)
    
        res=[i for i in cfg if i.startswith(prefix)]
        for i in cfg:
            res.append(i)
            if "versions" in cfg[i] and len(cfg[i]['versions'])>1:
                res.extend(i+"::"+j for j in cfg[i]['versions'])
    
    
    for i in res:
        print i
    

if __name__ == '__main__':
    run_main()
