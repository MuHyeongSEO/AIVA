import os
import shutil
import torch
import requests
from tqdm import tqdm
import zipfile
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

class Custom_TTS:
    def __init__(self, model_path='checkpoints_v2', output_path='output'):
        self.model_path = model_path
        self.result_cnt = 0
        self.output_path = output_path

        # cuda 확인
        self.check_cuda()

        # output 폴더 삭제 후 시작
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path)

    def check_cuda(self):
        '''cuda 환경 확인'''
        self.device = "cuda:0" if torch.cuda.is_available() else "Success"
        print(f'사용 환경(cude): {self.device}')

    def checkpoint_download(self):
        if os.path.exists(self.model_path) == False:
            download = Down_and_extract()
            ret = download.do(url="https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip", filename="checkpoints_v2_0417.zip")
            if ret == False:
                with open('./error_txt.txt', 'r', encoding='utf-8-sig') as f:
                    error_txt = f.read()
                    print(error_txt)

    def set_model(self, language='KR'):
        '''
        모델 설정
        language: 언어 입력(en-au, en-br, en-default, en-india, en-newest, en-us, es, fr, jp, KR, zh) 지원하는 패치 영역
        '''
        self.language = language
        
        # pre-trained 모델 다운로드
        self.checkpoint_download()

        # 톤 변경 모델 로드
        self.tone_color_converter = ToneColorConverter(f'{self.model_path}/converter/config.json', device=self.device)
        self.tone_color_converter.load_ckpt(f'{self.model_path}/converter/checkpoint.pth')
        print('톤 변경 모델 로드 완료')

        # TTS 모델 선언
        self.tts_model = TTS(language=self.language, device=self.device)
        print('TTS 모델 로드 완료')

        speaker_ids = self.tts_model.hps.data.spk2id
        for speaker_key in speaker_ids.keys():
            self.speaker_id = speaker_ids[speaker_key]
            speaker_key = speaker_key.lower().replace('_', '-')
        self.source_se = torch.load(f'{self.model_path}/base_speakers/ses/{speaker_key}.pth', map_location=self.device)
        print('음성 임베딩 완료')

    def get_reference_speaker(self, speaker_path, vad=True):
        # 톤 컬러 임베딩
        self.target_se, audio_name = se_extractor.get_se(speaker_path, self.tone_color_converter, vad=vad)
        print('목소리 톤 임베딩 완료')

    def make_speech(self, text, speed=1.1):
        try:
            # 경로 설정, 폴더 생성
            src_path = f'{self.output_path}/tmp.wav'
            os.makedirs(self.output_path, exist_ok=True)

            # TTS 수행
            self.tts_model.tts_to_file(text, self.speaker_id, src_path, speed=speed)
            print('TTS 생성 완료')

            # 목소리 변조 수행
            self.tone_color_converter.convert(audio_src_path=src_path, 
                                            src_se=self.source_se, 
                                            tgt_se=self.target_se, 
                                            output_path=f'{self.output_path}/result_{self.result_cnt}.wav')
            print('목소리 변조 완료')
            self.result_cnt += 1
        except Exception as e:
            print(e)

class Down_and_extract:
    def do(self, url, filename):
        try:
            # HTTP 응답에서 Content-Length(파일 크기) 가져오기
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            # 다운로드 진행을 표시하는 tqdm 설정
            with open(filename, "wb") as file, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))

            print(f"{filename} 다운로드 완료!")

            # 압축 해제 진행률 표시
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                # 압축된 파일의 전체 크기를 계산
                total_unzipped_size = sum((zinfo.file_size for zinfo in zip_ref.infolist()))

                # 압축 해제 진행률을 표시하는 tqdm 설정
                with tqdm(total=total_unzipped_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Extracting") as bar:
                    for zinfo in zip_ref.infolist():
                        extracted_file_path = zip_ref.extract(zinfo, './')
                        # 압축 해제된 파일 크기만큼 진행률을 업데이트
                        bar.update(zinfo.file_size)
            print(f"{filename} 압축 해제 완료!")
            return True
        except Exception as e:
            print(f'압축 해제 문제 발생: \n{e}')
            return False