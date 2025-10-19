import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from queue import Queue, Empty # Importa Empty explicitamente
import subprocess # Para executar o .exe
import re # Para limpar a mensagem de erro e URLs
import sys # Para fallback do diretório base

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x350") # Altura reduzida
        self.root.resizable(False, False)

        # --- Caminhos para os EXEs ---
        try:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.dirname(self.script_dir)
        except NameError:
             self.script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
             self.base_dir = os.path.dirname(self.script_dir)


        self.YTDLP_EXE_PATH = os.path.join(self.base_dir, "DEPENDENCIAS", "yt-dlp.exe")
        self.FFMPEG_EXE_PATH = os.path.join(self.base_dir, "DEPENDENCIAS", "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")
        self.FFMPEG_DIR_PATH = os.path.dirname(self.FFMPEG_EXE_PATH) # Apenas o diretório

        # --- Verificação Inicial ---
        if not os.path.exists(self.YTDLP_EXE_PATH):
             messagebox.showerror("Erro Crítico", f"yt-dlp.exe não encontrado em:\n{self.YTDLP_EXE_PATH}\n\nO programa não pode funcionar sem ele.")
             root.destroy()
             return
        if not os.path.exists(self.FFMPEG_EXE_PATH):
            messagebox.showwarning("Aviso de Dependência",
                f"Não foi possível encontrar o FFmpeg em:\n{self.FFMPEG_EXE_PATH}\n\n"
                "Downloads de áudio (MP3) e a junção de vídeo e áudio podem falhar.")
        else:
            print(f"yt-dlp.exe encontrado: {self.YTDLP_EXE_PATH}")
            print(f"FFmpeg encontrado: {self.FFMPEG_EXE_PATH}")
        # --- Fim da Verificação ---

        # Configurações
        self.settings_file = os.path.join(self.script_dir, "yt_downloader_settings.json") # Salva config na pasta SCRIPT
        self.download_folder = ""
        self.load_settings()

        # Variáveis de controle
        self.downloading = False
        self.progress_queue = Queue()
        self.download_process = None # Para tentar cancelar

        # Mapa de qualidades de vídeo para flags do yt-dlp
        self.video_quality_map = {
            "Melhor (1080p+)": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "Média (720p)": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "Pior (480p)": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
        }

        # Criar interface
        self.create_widgets()

        # Verificar atualizações de progresso
        self.check_progress()

        # Configurar estado inicial da UI
        self.toggle_quality_menu()

    def load_settings(self):
        """Carrega as configurações salvas"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    self.download_folder = settings.get("download_folder", "")
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                self.download_folder = ""
        # Define um padrão se não houver configuração ou for inválida
        if not self.download_folder or not os.path.isdir(self.download_folder):
             self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
             print(f"Pasta de download definida como padrão: {self.download_folder}")


    def save_settings(self):
        """Salva as configurações"""
        settings = {
            "download_folder": self.download_folder
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")


    def create_widgets(self):
        """Cria os elementos da interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="URL do YouTube:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))

        options_frame = ttk.LabelFrame(main_frame, text="Opções de Download", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))

        # --- Tipo de Download ---
        ttk.Label(options_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.download_type = tk.StringVar(value="video")
        ttk.Radiobutton(options_frame, text="Vídeo", variable=self.download_type, value="video", command=self.toggle_quality_menu).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(options_frame, text="Áudio (MP3)", variable=self.download_type, value="audio", command=self.toggle_quality_menu).grid(row=0, column=2, sticky=tk.W, padx=5)

        # --- Seleção de Qualidade (Simplificada) ---
        ttk.Label(options_frame, text="Qualidade:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(10,0))

        self.quality_var = tk.StringVar(value="Melhor (1080p+)")
        quality_options = list(self.video_quality_map.keys()) # Pega as chaves do nosso mapa
        self.quality_menu = ttk.OptionMenu(options_frame, self.quality_var, quality_options[0], *quality_options)
        self.quality_menu.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(10,0))

        # --- Pasta de Destino ---
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(10, 10))

        ttk.Label(dest_frame, text="Pasta de destino:").pack(side=tk.LEFT)
        self.dest_entry = ttk.Entry(dest_frame, width=40)
        self.dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.dest_entry.insert(0, self.download_folder) # Insere a pasta carregada ou padrão

        browse_btn = ttk.Button(dest_frame, text="Procurar", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        # --- Progresso ---
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="10")
        self.progress_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        self.stats_label = ttk.Label(self.progress_frame, text="Pronto para baixar")
        self.stats_label.pack(pady=(5, 0))

        # --- Botões ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky=tk.E)

        self.download_btn = ttk.Button(btn_frame, text="Baixar", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Botão Sair/Cancelar
        self.cancel_btn = ttk.Button(btn_frame, text="Sair", command=self.cancel_or_exit)
        self.cancel_btn.pack(side=tk.LEFT)


        main_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

    def toggle_quality_menu(self):
        """Habilita/Desabilita o menu de qualidade baseado na seleção de Vídeo/Áudio"""
        if self.download_type.get() == "audio":
            self.quality_menu.config(state=tk.DISABLED)
        else: # Vídeo
            self.quality_menu.config(state=tk.NORMAL)

    def browse_folder(self):
        """Abre o diálogo para selecionar pasta de destino"""
        # Sugere a pasta atual como inicial
        initial_dir = self.download_folder if os.path.isdir(self.download_folder) else os.path.expanduser("~")
        folder = filedialog.askdirectory(initialdir=initial_dir)
        if folder:
            self.download_folder = folder
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)
            self.save_settings()

    def _clean_url(self, url):
        """Limpa a URL para manter apenas o ID do vídeo, removendo ?si, &list, etc."""
        match = re.search(r'(?:v=|\/be\/|watch\?v=)([a-zA-Z0-9_-]{11})', url)
        if match:
            video_id = match.group(1)
            clean_url = f'https://www.youtube.com/watch?v={video_id}'
            print(f"URL limpa: {clean_url}")
            return clean_url
        return url

    def start_download(self):
        """Inicia o download em uma thread separada"""
        if self.downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL")
            return

        if not self.download_folder or not os.path.isdir(self.download_folder):
             # Tenta criar a pasta se não existir
            try:
                os.makedirs(self.download_folder, exist_ok=True)
                print(f"Pasta de destino criada: {self.download_folder}")
            except Exception as e:
                messagebox.showerror("Erro", f"Pasta de destino inválida ou não pôde ser criada:\n{self.download_folder}\n\n{e}")
                return

        if not os.path.exists(self.FFMPEG_EXE_PATH) and self.download_type.get() != 'video_simplest': # Adaptar se tiver opção sem ffmpeg
             if not messagebox.askyesno("Aviso FFmpeg", f"FFmpeg não encontrado em:\n{self.FFMPEG_EXE_PATH}\n\nDownloads de áudio MP3 e vídeos com a melhor qualidade podem falhar ou ficar sem som.\nDeseja continuar mesmo assim?"):
                 return

        self.downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(text="Cancelar") # Muda o botão para Cancelar
        self.progress_bar["value"] = 0
        self.stats_label.config(text="Preparando download...")

        download_type = self.download_type.get()

        format_string = None
        if download_type == "video":
            selected_quality_name = self.quality_var.get()
            format_string = self.video_quality_map.get(selected_quality_name)

        clean_url = self._clean_url(url)

        Thread(target=self.run_download, args=(clean_url, download_type, format_string), daemon=True).start()

    def run_download(self, url, download_type, format_string):
        """Executa o download usando yt-dlp.exe"""
        try:
            cmd = [
                self.YTDLP_EXE_PATH,
                '--no-playlist',
                '--progress', # Habilita a saída de progresso
                '--newline', # Garante uma linha por atualização
                '--no-check-certificate',
                '--restrict-filenames',
                 # Caminho de saída com padrão de nome
                '-o', os.path.join(self.download_folder, '%(title)s.%(ext)s'),
            ]

            # Adiciona localização do FFmpeg se existir
            if os.path.exists(self.FFMPEG_DIR_PATH):
                cmd.extend(['--ffmpeg-location', self.FFMPEG_DIR_PATH])
            else:
                 print("AVISO: Diretório do FFmpeg não encontrado. Conversões podem falhar.")


            if download_type == "audio":
                cmd.extend([
                    '-x', # Extrair áudio
                    '--audio-format', 'mp3',
                    '--audio-quality', '0', # Melhor qualidade VBR
                    '-f', 'bestaudio/best', # Baixa apenas o melhor áudio
                ])
            else: # Vídeo
                if not format_string: # Fallback
                    format_string = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                cmd.extend([
                    '-f', format_string,
                    '--merge-output-format', 'mp4',
                    # Argumentos para o pós-processador FFmpeg para corrigir áudio
                    '--postprocessor-args', 'ffmpeg:-vcodec copy -acodec aac -strict -2'
                ])

            cmd.append(url) # Adiciona a URL no final

            print("Executando comando:", subprocess.list2cmdline(cmd)) # Para depuração

            # Cria o processo
            # Precisamos do 'creationflags' no Windows para não abrir janela console
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            self.download_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Redireciona erros para a saída padrão
                universal_newlines=True,
                encoding='utf-8', # Tenta UTF-8
                errors='replace', # Substitui caracteres que não podem ser decodificados
                bufsize=1, # Line buffered
                creationflags=creationflags
            )

            # Processa a saída linha por linha
            output_log = [] # Guarda as últimas linhas de saída para erro
            for line in self.download_process.stdout:
                if not self.downloading: # Verifica se foi cancelado
                    print("Download cancelado pelo usuário.")
                    break
                line = line.strip()
                output_log.append(line)
                if len(output_log) > 20: output_log.pop(0) # Mantém apenas as últimas 20 linhas
                # print(line) # Debug: mostra todas as linhas

                if "[download]" in line and "%" in line:
                    try:
                        # Extrai porcentagem (ex: "[download]  10.3% of ...")
                        percentage_str = line.split('%')[0].split()[-1]
                        percentage = float(percentage_str)
                        self.progress_queue.put(("progress", percentage))

                        # Tenta extrair outras informações (velocidade, ETA)
                        parts = line.split('ETA')
                        eta_str = parts[-1].strip() if len(parts) > 1 else ""
                        speed_match = re.search(r'at\s+([0-9.]+\s*[KMGT]?i?B/s)', line)
                        speed_str = speed_match.group(1).strip() if speed_match else ""
                        stats_msg = f"Baixando: {percentage:.1f}%"
                        if speed_str: stats_msg += f" | {speed_str}"
                        if eta_str: stats_msg += f" | ETA: {eta_str}"
                        self.progress_queue.put(("stats", stats_msg))

                    except ValueError:
                        self.progress_queue.put(("stats", line)) # Mostra a linha se o parse falhar
                    except Exception as parse_e:
                        print(f"Erro ao parsear linha de progresso: {parse_e} -> {line}")
                        self.progress_queue.put(("stats", line))
                elif line:
                     # Mostra outras linhas importantes (merge, conversão, erros)
                    if "Merging formats" in line:
                         self.progress_queue.put(("stats", "Juntando vídeo e áudio..."))
                    elif "Deleting original file" in line:
                         pass # Ignora
                    elif "Extracting audio" in line:
                         self.progress_queue.put(("stats", "Extraindo e convertendo áudio para MP3..."))
                    elif "[ExtractAudio]" in line and 'Destination: ' in line:
                         self.progress_queue.put(("stats", "Conversão para MP3 concluída."))
                    elif "[Merger]" in line and 'into' in line:
                         self.progress_queue.put(("stats", "Junção de áudio/vídeo concluída."))
                    #elif "Destination:" in line:
                    #     self.progress_queue.put(("stats", "Download concluído, processando..."))
                    elif "ERROR:" in line:
                         # Manda a mensagem de erro para a UI
                         clean_error = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', line.replace("ERROR:", "").strip())
                         self.progress_queue.put(("error", f"yt-dlp: {clean_error}"))
                    elif self.downloading: # Evita mostrar mensagens residuais após cancelar
                         # Mostra outras linhas genéricas de status
                         if not line.startswith("[") and not line.startswith("WARNING:"):
                              self.progress_queue.put(("stats", line))


            self.download_process.wait() # Espera o processo terminar

            if self.downloading: # Se não foi cancelado
                if self.download_process.returncode == 0:
                    # Verifica se um erro não foi reportado antes de declarar sucesso
                    if "error" not in [item[0] for item in list(self.progress_queue.queue)]:
                        self.progress_queue.put(("complete", "Download concluído com sucesso!"))
                    else:
                        # Um erro foi reportado no stdout, mas o código de saída foi 0? Estranho.
                        print("Download finalizado com código 0, mas um erro foi detectado na saída.")
                        self.progress_queue.put(("error_done", "Download concluído, mas um erro foi reportado durante o processo."))

                else:
                    # Se um erro não foi capturado no stdout, mostra as últimas linhas
                     last_output = "\n".join(output_log)
                     error_msg = f"Download falhou (código: {self.download_process.returncode}).\n\nÚltima saída:\n{last_output}"
                     # Envia para a UI apenas se nenhum erro específico foi enviado antes
                     if "error" not in [item[0] for item in list(self.progress_queue.queue)]:
                          self.progress_queue.put(("error_done", error_msg))
                     else: # Apenas loga no console
                          print(f"Download falhou (código: {self.download_process.returncode}), erro já reportado.")


        except FileNotFoundError:
             self.progress_queue.put(("error", f"Erro: yt-dlp.exe não encontrado em {self.YTDLP_EXE_PATH}"))
        except Exception as e:
            error_message = str(e)
            clean_error = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', error_message)
            import traceback
            detailed_error = f"{clean_error}\n\nTraceback:\n{traceback.format_exc()}"
            self.progress_queue.put(("error", f"Erro inesperado: {detailed_error}"))
        finally:
            self.download_process = None
            self.progress_queue.put(("done",)) # Sinaliza que a thread terminou

    def check_progress(self):
        """Verifica a fila de progresso e atualiza a interface"""
        try:
            while True:
                item = self.progress_queue.get_nowait()
                msg_type, msg_data = item[0], item[1] if len(item) > 1 else None

                if msg_type == "progress":
                    if isinstance(msg_data, (int, float)): self.progress_bar["value"] = msg_data

                elif msg_type == "stats":
                     if isinstance(msg_data, str): self.stats_label.config(text=msg_data)

                elif msg_type == "complete":
                    self.progress_bar["value"] = 100
                    self.stats_label.config(text="Concluído!")
                    message = msg_data if isinstance(msg_data, str) else "Download concluído!"
                    messagebox.showinfo("Sucesso", message)
                    self.reset_ui(download_finished=True)

                elif msg_type == "error":
                    message = msg_data if isinstance(msg_data, str) else "Erro desconhecido."
                    messagebox.showerror("Erro no Download", message)
                    self.reset_ui(download_finished=False)

                elif msg_type == "error_done":
                     message = msg_data if isinstance(msg_data, str) else "Download falhou."
                     print(message) # Log no console
                     # Mostra uma msg genérica se nenhum erro específico apareceu antes
                     if "error" not in [i[0] for i in list(self.progress_queue.queue)]:
                          messagebox.showerror("Erro no Download", message)
                     self.reset_ui(download_finished=False)

                elif msg_type == "done":
                    self.downloading = False
                    # Garante reset da UI no final, caso não tenha sido feito por 'complete' ou 'error'
                    self.reset_ui(download_finished=False)


        except Empty: # Captura explicitamente Queue.Empty
            pass # Fila vazia
        except Exception as e:
            print(f"ERRO inesperado em check_progress: {e}")
            import traceback
            traceback.print_exc()

        # Reagenda a verificação
        self.root.after(100, self.check_progress)

    def cancel_or_exit(self):
        """Cancela o download ou sai do programa"""
        if self.downloading and self.download_process:
            if messagebox.askyesno("Cancelar Download", "Tem certeza que deseja cancelar o download em andamento?"):
                self.downloading = False # Sinaliza para a thread parar de processar
                try:
                    # Tenta terminar o processo yt-dlp
                    print(f"Tentando cancelar o processo: {self.download_process.pid}")
                    self.download_process.terminate() # Envia SIGTERM (mais gentil)
                    try:
                        # Espera um pouco para ver se termina
                        self.download_process.wait(timeout=2)
                        print("Processo terminado.")
                    except subprocess.TimeoutExpired:
                        # Se não terminou, força (SIGKILL)
                        print("Processo não terminou, forçando...")
                        self.download_process.kill()
                        self.download_process.wait() # Espera a morte
                        print("Processo forçado a terminar.")

                except ProcessLookupError:
                     print("Processo já havia terminado.")
                except Exception as e:
                    print(f"Erro ao tentar cancelar o processo: {e}")
                finally:
                    self.download_process = None
                    self.reset_ui(download_finished=False)
                    self.stats_label.config(text="Download cancelado.")
        else:
            self.root.destroy() # Sai do programa


    def reset_ui(self, download_finished=False):
        """Reseta a interface após o download ou erro"""
        self.downloading = False
        self.progress_bar["value"] = 0
        self.stats_label.config(text="Pronto para baixar")

        if download_finished:
            self.url_entry.delete(0, tk.END)

        # Garante que os botões voltem ao estado inicial
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(text="Sair")
        self.toggle_quality_menu()

# --- Função run_update_check ---
def run_update_check():
     """Roda o update check em uma thread para não travar a UI"""
     try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
     except NameError:
         try: base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
         except Exception: base_dir = "."

     ytdlp_exe = os.path.join(base_dir, "DEPENDENCIAS", "yt-dlp.exe")

     if os.path.exists(ytdlp_exe):
        print("Verificando atualizações para yt-dlp.exe...")
        try:
            update_cmd = [ytdlp_exe, "-U"]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(update_cmd, capture_output=True, text=True, check=False,
                                    creationflags=creationflags, encoding='utf-8', errors='replace')
            output = result.stdout or result.stderr

            if result.returncode == 0:
                if "yt-dlp is up to date" in output:
                    print("yt-dlp.exe já está atualizado.")
                elif "Updated yt-dlp to" in output:
                    print("yt-dlp.exe atualizado com sucesso!")
                    print(output)
                else:
                     print(f"Resultado inesperado da atualização (código 0):\n{output}")
            else:
                 clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output)
                 print(f"AVISO: Falha ao verificar atualização do yt-dlp.exe (código: {result.returncode}).")
                 print(clean_output)

        except Exception as e: print(f"AVISO: Erro no update check: {e}")
     else: print(f"AVISO: yt-dlp.exe não encontrado em '{ytdlp_exe}' para auto-update.")
# --- Fim run_update_check ---


if __name__ == "__main__":
    # Roda a verificação de update em background
    Thread(target=run_update_check, daemon=True).start()

    print("Iniciando a interface gráfica...")
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()