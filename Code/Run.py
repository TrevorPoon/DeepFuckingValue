import subprocess

# Command 1: cd code
subprocess.run(['cd', 'code'], shell=True)

# Command 2: streamlit run Streamlit_Bloomberg_Terminal.py
subprocess.run(['streamlit', 'run', 'Streamlit_Bloomberg_Terminal.py'], shell=True)