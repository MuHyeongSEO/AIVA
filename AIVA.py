import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
import os
import threading
from custom_tts import Custom_TTS
import pygame

class TTS_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AIVA TTS")
        self.root.geometry("500x400")
        self.background_color = (0, 128, 255)
        
        # TTS 모듈 초기화
        self.tts_module = Custom_TTS()
        self.tts_module.set_model()

        # pygame 초기화
        pygame.mixer.init()

        # 샘플 화자 음성 파일 입력
        self.label_sample = tk.Label(root, text="음성 파일 경로:")
        self.label_sample.pack()
        self.entry_sample = tk.Entry(root, width=40)
        self.entry_sample.pack()
        self.btn_browse = tk.Button(root, text="파일 업로드", command=self.browse_file)
        self.btn_browse.pack()

        self.btn_load_sample = tk.Button(root, text="음성 학습", command=self.load_sample_voice)
        self.btn_load_sample.pack()

        # 텍스트 입력
        self.label_text = tk.Label(root, text="문장 입력")
        self.label_text.pack()
        self.entry_text = tk.Entry(root, width=40)
        self.entry_text.pack()

        self.btn_generate_tts = tk.Button(root, text="음성 합성", command=self.generate_tts)
        self.btn_generate_tts.pack()

        # TTS 음성 재생 버튼
        self.btn_play_tts = tk.Button(root, text="음성 출력", command=self.play_tts)
        self.btn_play_tts.pack()

        # 출력 창
        self.output_text = scrolledtext.ScrolledText(root, height=10, width=50)
        self.output_text.pack()

        self.log("시스템이 정상 작동중입니다.")

    def log(self, message):
        """출력창에 로그 메시지를 추가하는 함수"""
        self.output_text.insert(tk.END, message + '\n')
        self.output_text.see(tk.END)

    def browse_file(self):
        """사용자가 샘플 음성 파일을 선택할 수 있도록 파일 다이얼로그를 여는 함수"""
        file_path = filedialog.askopenfilename(
            title="음성 파일을 선택",
            filetypes=(("MP3 files", "*.mp3;*.wav;*.acc;*.m4a"), ("All files", "*.*"))
        )
        if file_path:
            self.entry_sample.delete(0, tk.END)
            self.entry_sample.insert(0, file_path)

    def load_sample_voice(self):
        """샘플 음성 파일을 로드하여 화자의 목소리를 임베딩"""
        sample_path = self.entry_sample.get()
        if os.path.exists(sample_path):
            self.log(f"샘플 음성을 로드 중입니다. {sample_path}")
            self.tts_module.get_reference_speaker(speaker_path=sample_path)
            self.log("샘플 음성을 성공적으로 로드했습니다.")
        else:
            messagebox.showerror("Error", "샘플 음성 파일이 로드가 안되었습니다.")

    def generate_tts(self):
        """입력된 텍스트로 TTS 생성"""
        text = self.entry_text.get()
        if text:
            self.log(f"문장 학습중... {text}")
            threading.Thread(target=self._tts_thread, args=(text,)).start()
        else:
            messagebox.showerror("Error", "문장을 입력해주세요")

    def _tts_thread(self, text):
        """TTS 생성 비동기 작업"""
        try:
            self.tts_module.make_speech(text)
            self.log("TTS generation completed.")
        except Exception as e:
            self.log(f"Error generating TTS: {e}")

    def play_tts(self):
        """생성된 TTS 음성을 재생"""
        tts_path = f'./output/result_{self.tts_module.result_cnt-1}.wav'
        
        if os.path.exists(tts_path):
            self.log("음성을 출력중입니다.")
            pygame.mixer.music.load(tts_path)  # 음성 파일 로드
            pygame.mixer.music.play()  # 음성 재생

            # 재생 완료 후 파일 해제 처리
            while pygame.mixer.music.get_busy():  # 음악이 재생 중인지 확인
                continue  # 재생 중이라면 계속 기다림

            # 재생이 끝난 후 stop 호출 (명시적으로)
            pygame.mixer.music.stop()  # 파일 사용 해제
            self.log("음성 출력 및 저장 되었습니다.")
        else:
            messagebox.showerror("Error", "문장 학습이 안되었습니다. 문장 학습부터 진행 부탁드립니다.")



if __name__ == "__main__":
    root = tk.Tk()
    app = TTS_GUI(root)
    root.mainloop()
