# Baixar Videos YouTube 💾​

*Um aplicativo desktop simples e prático para baixar vídeos e músicas do YouTube com facilidade.*

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=for-the-badge&logo=python)
![Plataforma](https://img.shields.io/badge/Plataforma-Windows-lightgrey?style=for-the-badge&logo=windows)
![yt-dlp](https://img.shields.io/badge/Dependência-yt--dlp.exe-orange?style=for-the-badge)
![FFmpeg](https://img.shields.io/badge/Dependência-FFmpeg-blueviolet?style=for-the-badge)


> [!WARNING]
> ### ⚠️ Aviso Importante e Declaração de Responsabilidade
>
> 1.  **TERMOS DE SERVIÇO DO YOUTUBE:** Baixar vídeos do YouTube pode violar os [Termos de Serviço](https://www.youtube.com/static?template=terms) da plataforma. Este aplicativo é fornecido para fins educacionais e de conveniência pessoal.
> 2.  **DIREITOS AUTORAIS:** Respeite os direitos autorais. Não utilize este aplicativo para baixar ou distribuir material protegido sem a permissão explícita do detentor dos direitos.
> 3.  **USO POR SUA CONTA E RISCO:** O autor não se responsabiliza por qualquer uso indevido do aplicativo ou por quaisquer consequências (legais ou técnicas) resultantes do seu uso. Você assume total responsabilidade pelas suas ações.

---

### 📌 Principais Funcionalidades

-   ✅ **Download de Vídeo:** Baixa vídeos do YouTube no formato MP4, com áudio convertido para AAC para máxima compatibilidade.
-   ✅ **Extração de Áudio:** Extrai e converte o áudio de vídeos diretamente para o formato MP3.
-   ✅ **Seleção de Qualidade Simplificada:** Escolha entre "Melhor (1080p+)", "Média (720p)" ou "Pior (480p)" para vídeos.
-   ✅ **Interface Intuitiva:** Janela simples e direta ao ponto, desenvolvida com Tkinter.
-   ✅ **Progresso Visual:** Barra de progresso e status em tempo real (velocidade, ETA).
-   ✅ **Auto-Atualização:** O `yt-dlp.exe` verifica e se atualiza automaticamente ao iniciar, garantindo maior chance de compatibilidade contínua com o YouTube.
-   ✅ **Portabilidade:** Funciona em qualquer PC Windows, desde que a estrutura de pastas das dependências seja mantida.
-   ✅ **Sem Complicações:** Não requer login, cookies ou configurações complexas de navegador.

### ⚙️ Pré-requisitos

* **Python 3:** Necessário para executar o script. A biblioteca Tkinter geralmente já vem incluída no Windows. [Download Python](https://www.python.org/downloads/)
* **`yt-dlp.exe`:** O "cérebro" do download. **Deve** estar na pasta `DEPENDENCIAS`. [Download yt-dlp.exe](https://github.com/yt-dlp/yt-dlp/releases/latest)
* **`ffmpeg.exe`:** Essencial para converter áudio (MP3/AAC) e juntar arquivos. **Deve** estar na subpasta correta dentro de `DEPENDENCIAS`. [Download FFmpeg (Builds Gyan.dev)](https://www.gyan.dev/ffmpeg/builds/) (Baixe `ffmpeg-release-essentials.zip` ou `full.zip`, extraia e copie o conteúdo da pasta `bin`).

### 🔧 Instalação e Estrutura de Pastas

1.  **Baixe ou Clone:** Obtenha os arquivos do projeto.
2.  **Crie a Estrutura (CRÍTICO!):** Organize as pastas e arquivos **exatamente** assim:

    ```
    YOUTUBE VIDEO BAIXAR/   <-- Pasta principal (ou o nome que preferir)
    ├── DEPENDENCIAS/
    │   ├── yt-dlp.exe
    │   └── ffmpeg-master-latest-win64-gpl-shared/  <-- Nome da pasta do FFmpeg (PODE VARIAR!)
    │       └── bin/
    │           ├── ffmpeg.exe
    │           ├── ffplay.exe   (opcional)
    │           └── ffprobe.exe  (opcional)
    └── SCRIPT/
        └── youtubeTetse.py       <-- Seu script Python
        └── yt_downloader_settings.json  <-- Será criado automaticamente
    ```
    > Se o nome da pasta onde você extraiu o FFmpeg for diferente de `ffmpeg-master-latest-win64-gpl-shared`, você **PRECISA** editar a linha `self.FFMPEG_EXE_PATH` dentro do arquivo Python (`youtubeTetse.py`) para refletir o nome correto da pasta!

### 🚀 Como Executar

1.  **Abra o Terminal:** Navegue até a pasta principal (`YOUTUBE VIDEO BAIXAR`) usando o Prompt de Comando ou PowerShell.
2.  **Execute o Script:** Digite o comando:
    ```bash
    python SCRIPT/youtubeTetse.py
    ```
    *(Ajuste `youtubeTetse.py` se o nome do seu arquivo for diferente)*.
3.  **Aguarde a Atualização (se houver):** Na primeira vez ou se houver uma nova versão, o `yt-dlp.exe` pode levar alguns segundos para se atualizar (você verá mensagens no terminal).
4.  **Use o Aplicativo:**
    * Cole a URL do vídeo do YouTube.
    * Escolha "Vídeo" ou "Áudio (MP3)".
    * Se for vídeo, selecione a qualidade desejada.
    * Clique em "Procurar" para definir onde salvar o arquivo (padrão: pasta Downloads).
    * Clique em "Baixar".

### 💡 Como Funciona (Resumo Técnico)

* **Interface:** Tkinter (biblioteca gráfica padrão do Python).
* **Motor de Download:** `yt-dlp.exe` (executável externo, atualizado automaticamente).
* **Processamento de Mídia:** `ffmpeg.exe` (executável externo).
* **Comunicação:** Módulo `subprocess` do Python para chamar os `.exe`.
* **Interface Responsiva:** `threading` e `queue` para rodar o download em segundo plano sem travar a janela.
* **Configuração:** Um arquivo `json` simples para lembrar a última pasta de download.
* **Portabilidade:** Caminhos relativos calculados com `os.path` para encontrar as dependências.
