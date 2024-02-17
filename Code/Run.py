import subprocess
import os

parent_dir = os.path.dirname(os.path.abspath(__file__))

process = subprocess.Popen(["streamlit", "run", os.path.join(
            parent_dir, 'Streamlit_Bloomberg_Terminal.py')])
