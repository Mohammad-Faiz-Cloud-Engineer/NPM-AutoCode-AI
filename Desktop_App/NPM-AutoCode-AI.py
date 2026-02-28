import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QProgressBar
)
from PySide6.QtCore import QThread, Signal
from langchain_core.prompts import PromptTemplate
from npmai import Ollama,Memory
from langchain_core.output_parsers import StrOutputParser
import traceback
import subprocess
import os

# =======================
# WORKER THREAD
# =======================
class CodeWorker(QThread):
    log = Signal(str)
    finished = Signal(str)

    def __init__(self, task_text):
        super().__init__()
        self.task_text = task_text
        self.code_var= {}
    
    def executor(self,code):
      error_log=""
      try:
        exec(code,self.code_var)
        return None
      except Exception as e:
        error_log+= traceback.format_exc()
        return error_log

    def run(self):
      self.log.emit("npmai is doing your requested task")
      memory=Memory("coder0-generator")
      memory1=Memory("safety_checker")
      
      llm=Ollama(
          model="codellama:7b-instruct",
          temperature=0.3
      )
      
      query=self.task_text

      prompt = f"""
      Hey you are helpful code assistant that writes code just write code nothing else
      and maintain proper indentation. No extra explanations.
      remember that whatever imports you are using install dependencies in code using subprocess beacuase user had not installed your code requirements
      Do not respond with any insturction or any other statement if you are giving any statement in english or that is not of code so give in # comment ok beacuase your code will be executed through exec() function of python so give such format code that can be executed in exec() function YOUR WHOLE RESPONSE WILL BE SENT TO exec() so do not write anything except code.
      You will be asked to generate code about a task.
      This is the task:{query}"""
      
      response=llm.invoke(prompt)
      
      parser=StrOutputParser()
      final_response=parser.parse(response)
      
      cleaned_response = final_response.strip()
      if cleaned_response.startswith("```python"):
        cleaned_response = cleaned_response[len("```python"):]
      elif cleaned_response.startswith("```"):
        cleaned_response= cleaned_response[len("```"):]
      else:
        pass
        
      if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-len("```")]
        memory.save_context(query,cleaned_response)
        self.log.emit("Code generation for requested task is completed now")
        
      
      while True:
        history1=memory1.load_memory_variables()
        if "AI: " in history1:
          last_safety_decision= history1.split("AI: ")[-1].strip()
        else:
          last_safety_decision= "No"
        
        if "Yes" not in last_safety_decision:
          llm1=Ollama(
              model="qwen2.5-coder:7b",
              temperature=0.1
              )
          
          prompt=f"""
          [SYSTEM: SECURITY MONITOR]
          You are a senior cyber-security auditor. Analyze the Python code provided below for MALICIOUS intent or HIGH-RISK operations that could harm a non-technical user's system.

          CRITERIA FOR 'Yes' (High Risk):
          1. Deleting system files or user documents without clear task-related necessity.
          2. Stealing private data (passwords, cookies, SSH keys, .env files).
          3. Establishing unauthorized remote connections (reverse shells).
          4. Commands that can crash the OS (Fork bombs, infinite resource loops).
          5. Obfuscated or hidden code intended to bypass detection.

          CRITERIA FOR 'No' (Safe):
          1. Standard data processing, plotting, or web scraping as per user task.
          2. Creating/Writing files specifically requested by the task.
          3. Installing standard libraries via pip/subprocess.
          
          CODE TO REVIEW:
          {cleaned_response}
          
          OUTPUT INSTRUCTION:
          Is this code dangerous? Respond ONLY with exactly one word: 'Yes' or 'No'.
          Do not provide any explanation, warnings, or markdown.
          """
           
          response=llm1.invoke(prompt)
          if response=="Yes":
            self.finished.emit("!!! SECURITY RISK !!! Review code. To bypass, click on Execute again without changing prompt")
            memory1.save_context("Latest_AI_Response",response)
            return

          error_log = self.executor(cleaned_response)

          if not error_log:
            self.finished.emit("--- Task Completed Successfully. ---")
            break

          self.log.emit("--- Execution Have Some Problem. Capturing Error and Debugging... ---")

          history=memory.load_memory_variables()
          response1=llm.invoke(f"""
          Hey, you wrote this code: {history.split("AI: ")[-1].strip()}
          The user task is: {query}
          During execution, we got this error: {error_log}
                               
          Your Goal: Fix the error and complete the task.
          You have two choices:
          1. REWRITE: If the logic is fundamentally wrong, rewrite the WHOLE code.
          2. PARTIAL: If some task is already done (variables are saved in globals()), you can write just the remaining part to complete the task. Only do this if you are 100% confident.

          IMPORTANT RULES:
          1. User is non-technical; handle everything automatically.
          2. Maintain proper indentation. No extra explanations outside of # comments.
          3. ALWAYS include subprocess imports/installs if you use new libraries.
          4. Output ONLY executable code. Do not say "Here is the fix".
          5. If writing a partial fix, assume previous successful variables are already in memory.
          """)

          final_response1=parser.parse(response1)

          cleaned_response = final_response1.strip()
          if cleaned_response.startswith("```python"):
            cleaned_response = cleaned_response[len("```python"):]
          elif cleaned_response.startswith("```"):
            cleaned_response= cleaned_response[len("```"):]
          else:
            pass
            
          if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-len("```")]
            memory.save_context(error_log,cleaned_response)


# =======================
# UI
# =======================
class AutoCodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NPM AutoCode AI")
        self.resize(600, 600)
        layout = QVBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Describe your automation task here...")

        self.done_btn = QPushButton("Generate & Execute")
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        layout.addWidget(QLabel("Task Description:"))
        layout.addWidget(self.task_input)
        layout.addWidget(self.done_btn)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_box)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.done_btn.clicked.connect(self.start_task)

    def start_task(self):
        task_text = self.task_input.text().strip()
        if not task_text:
            self.log_box.append("Please enter a task description")
            return

        self.log_box.append("Starting task...")
        self.progress_bar.setValue(10)

        self.worker = CodeWorker(task_text)
        self.worker.log.connect(self.log_box.append)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()

    def task_finished(self, msg):
        self.log_box.append(msg)
        self.progress_bar.setValue(100)

# =======================
# MAIN
# =======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoCodeApp()
    window.show()
    base_dir = os.path.dirname(sys.argv[0])
    for filename in ["coder0-generator.json", "safety_checker.json"]:
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                pass
    
    sys.exit(app.exec())
