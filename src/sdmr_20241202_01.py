# -*- coding: utf-8 -*-
"""SDMR_20241202_01.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17J3aSCy1moXkkZqwioKjZLCn1vD8bNXG

### StableDiffusionManager(CivitAIManager+Illustrious)
CivitAIBrowser+とIllustriousを実用速度で使えるようにする。

### 1. 全体環境設定とライブラリ読み込み
"""

# @title 初期設定
# 1. Google Driveをマウント
from google.colab import drive
drive.mount('/content/drive')

# 2. ライブラリのパスを追加
import sys
sys.path.append('/content/drive/My Drive/dev/src')
sys.path.append('/content/drive/My Drive/ColabLibraries')

import importlib
# 大抵のimport文はこれで大丈夫
from hd01 import *
# HD01に入力する環境変数
from hd01 import repo_folder, repo_url, CivitAI_api_key, init_checkpoint, drive_path, system_reset, flg_debug
# debug_helperを使えるようにする
from hd01 import debugger, initialize_debugger

debugger = initialize_debugger( debug = flg_debug )
debugger.debug_print("The environment setting were imported.")

from google.colab import drive
drive.mount('/content/drive')

"""###2. StableDiffusionManagerサブクラス定義"""

# @title ClsRepository
class ClsRepository:
    def __init__(self, repo_folder):
        """Stable Diffusionのリポジトリをクローン"""
        if repo_folder is not None:
            self.repo_folder = repo_folder
            debugger.debug_print("repo_folder :", self.repo_folder)
        else:
            debugger.debug_print("repo_folder is None")
            sys.exit(0)
    def clone_repository(self):
        if not os.path.exists(self.repo_folder):
            debugger.debug_print("Cloning Stable Diffusion repository...")
            # subprocess.run(["git", "clone", "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git", self.repo_folder], check=True)
            try:
                subprocess.run(["git", "clone", "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git", self.repo_folder], check=True)
            except subprocess.CalledProcessError as e:
                debugger.debug_print(f"Git clone failed: ", e)
                return False
        else:
            debugger.debug_print("Stable Diffusion repository already exists.")
        # subprocess.run( ["chmod", "+x", "/content/stable-diffusion-webui/webui-user.sh", self.repo_folder], check=True)
        try:
            subprocess.run( ["chmod", "+x", "/content/stable-diffusion-webui/webui-user.sh", self.repo_folder], check=True)
        except subprocess.CalledProcessError as e:
            debugger.debug_print(f"chmod +x failed: ", e)
            return False

# @title ClsDependencies
class ClsDependencies:
    def __init__(self, requirements):
        if requirements is not None:
            self.requirements = requirements
            debugger.debug_print("requirements: ", self.requirements )
        else:
            debugger.debug_print("requirements is None")
            sys.exit(0)

    def install_dependencies(self):
        """Install dependencies including torch, torchvision, torchaudio, xformers, pydantic, jedi, and fastapi."""

        # 1. requirements.txtに記載された依存関係のインストール
        self.install_dependencies_from_requirements()

        # 2. torchなどの追加モジュールのインストール
        self.install_torch_etc()

        # 3. xformersのインストール
        self.install_xformers()

        debugger.debug_print("All dependencies installed successfully.")


    def install_dependencies_from_requirements(self):
        debugger.debug_print("Installing dependencies from requirements.txt...")
        try:
            subprocess.run(
                # ["pip", "install", "-r", "/content/stable-diffusion-webui/requirements.txt"],
                ["pip", "install", "-r", self.requirements],
                check=True
            )
        except subprocess.CalledProcessError as e:
            debugger.debug_print(f"An error occurred while installing requirements.txt dependencies: ", e )
            return

        debugger.debug_print("Checking requirements.txt for necessary installations...")

        # 1. requirements.txtの内容を解析
        with open( self.requirements, "r") as f:
            requirements = {}
            for line in f:
                if "==" in line:
                    package, required_version = line.strip().split("==")
                    requirements[package] = required_version

        # 2. 各パッケージについてバージョンを確認し、必要な場合のみインストール
        for package, required_version in requirements.items():
            installed_version = self.check_installed_version(package)

            if installed_version:
                # バージョンを比較
                if version.parse(installed_version) >= version.parse(required_version):
                    debugger.debug_print( package, " is already at the required version ", installed_version, " (>= ", required_version, "). Skipping.")
                else:
                    debugger.debug_print( package, " is at version ", installed_version, ", upgrading to ", required_version, "...")
                    try:
                        subprocess.run(["pip", "install", f"{package}=={required_version}", "--upgrade"], check=True)
                    except subprocess.CalledProcessError as e:
                        debugger.debug_print(f"pip install failed: ", e)
                        return False
            else:
                debugger.debug_print( package, " is not installed, installing version ", required_version, "...")
                try:
                    subprocess.run(["pip", "install", f"{package}=={required_version}"], check=True)
                except subprocess.CalledProcessError as e:
                    debugger.debug_print(f"pip install failed: ", e)
                    return False

        # print("All necessary dependencies are up to date.")
        debugger.debug_print("All necessary dependencies are up to date.")

    def check_installed_version(self, package_name):
        # pip showコマンドを使って、特定のパッケージ情報を取得
        result = subprocess.run(["pip", "show", package_name], capture_output=True, text=True)

        if result.returncode != 0:
            # パッケージがインストールされていない場合
            return None

        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                # バージョン情報の行を探して、それを返す
                return line.split("Version: ")[1]

        return None

    def install_torch_etc(self):
        debugger.debug_print("Checking for torch, torchvision, torchaudio...")
        # 必要なパッケージとバージョン
        required_packages = {
            "torch": "2.2.2",
            "torchvision": "0.17.2",
            "torchaudio": "2.2.2"
        }

        # 各パッケージを確認してインストールまたはアップグレード
        for package, version in required_packages.items():
            self.install_or_upgrade(package, version)

        debugger.debug_print("Torch, torchvision, torchaudio are up-to-date.")

    def install_or_upgrade(self, package_name, required_version):
        installed_version = self.check_installed_version(package_name)

        # テストのためにプリント文を追加
        debugger.debug_print( "Checking package: ", package_name )
        debugger.debug_print( "Installed version: ", installed_version )
        debugger.debug_print( "Required version: ", required_version )

        if installed_version:
            if version.parse(installed_version) >= version.parse(required_version):
                debugger.debug_print( package_name, " is already at the required or newer version ", installed_version)
            else:
                debugger.debug_print( package_name, " is at version ", installed_version, ", upgrading to ", required_version, "...")
                # subprocess.run(["pip", "install", f"{package_name}=={required_version}", "--upgrade"], check=True)
                try:
                    subprocess.run(["pip", "install", f"{package_name}=={required_version}", "--upgrade"], check=True)
                except subprocess.CalledProcessError as e:
                    debugger.debug_print(f"pip install failed: ", e)
                    return False
        else:
            # print(f"{package_name} is not installed, installing version {required_version}...")
            debugger.debug_print( package_name, " is not installed, installing version ", required_version, "...")
            # subprocess.run(["pip", "install", f"{package_name}=={required_version}"], check=True)
            try:
                subprocess.run(["pip", "install", f"{package_name}=={required_version}"], check=True)
            except subprocess.CalledProcessError as e:
                debugger.debug_print(f"pip install failed: ", e)
                return False

    def install_xformers(self):
        # print("Checking for xformers...")
        debugger.debug_print("Checking for xformers...")
        try:
            # 既存のxformersをアンインストール
            subprocess.run(["pip", "uninstall", "-y", "xformers"], check=True)

            # 新しいxformersをインストール
            subprocess.run([
                "pip", "install", "xformers", "--index-url", "https://download.pytorch.org/whl/cu121"
            ], check=True)

            print("xformers installed successfully.")
            debugger.debug_print("xformers installed successfully.")

        except subprocess.CalledProcessError as e:
            print(f"An error occurred while installing xformers: {e}")
            debugger.debug_print( "An error occurred while installing xformers: ", e)
            self.handle_xformers_install_failure()

# @title ClsDrive
class ClsSystemReset:
    def __init__(self, system_reset):
        """
        Google Drive側のフォルダを消去するかどうかを確認し、処理を実行するメソッド。
        """
        if system_reset is not None:
            self.system_reset = system_reset
            debugger.debug_print( "system_reset is setted" )
        else:
            debugger.debug_print( "system_reset is None")
            sys.exit(0)

    def reset_drive_if_needed(self):
        # 1. system_resetを調べる
        if not self.system_reset:
            debugger.debug_print("system_reset が False のため、何も実行されません。")
            return

        # 2. 警告メッセージを表示
        self.warning_message = """
        警告: この操作により、Google Drive側のフォルダが完全に消去されます。
        本当に実行しますか？ (y/n)
        """
        self.user_response = input(self.warning_message)

        # 3. ユーザーが進んだ場合、再度警告を行う
        if self.user_response.lower() == 'y':
            self.second_warning = """
            最終警告: Google Drive側の全てのフォルダが消去されます。
            この操作は取り消せません。本当に実行しますか？ (y/n)
            """
            self.final_response = input(self.second_warning)

            # 4. ユーザーが再度進んだ場合、フォルダを消去
            if self.final_response.lower() == 'y':
                try:
                    # shutil.rmtree(self.drive_path)  # Google Drive側のフォルダを完全消去
                    debugger.debug_print(f"{self.drive_path} のフォルダを完全に消去しました。")
                except Exception as e:
                    debugger.debug_print(f"エラーが発生しました: {e}")
            else:
                debugger.debug_print("操作をキャンセルしました。フォルダは消去されません。")
        else:
            debugger.debug_print("操作をキャンセルしました。フォルダは消去されません。")

        # 5. system_resetをFalseに設定
        debugger.debug_print("事故防止のため、system_reset を False に設定してください。")
        input("続行するには何かキーを押してください")

# @title ClsCheckpoints
class ClsCheckpoints:
    def __init__(self, ckpt_dir, CivitAI_api_key):
        if ckpt_dir is not None or CivitAI_api_key is not None:
            self.ckpt_dir = ckpt_dir
            self.CivitAI_api_key = CivitAI_api_key
            debugger.debug_print("ckpt_dir :", ckpt_dir)
            self.ckpt_dir = ckpt_dir
        else:
            debugger.debug_print("ckpt_dir is None")
            sys.exit(0)

    def list_checkpoints(self):
        """インストールされているチェックポイントファイルを列挙する"""
        debugger.debug_print(f"****************************************************")
        debugger.debug_print(f"************  InstallされているCheckpoint  ***********")
        debugger.debug_print(f"****************************************************")

        try:
            # Checkpointファイルをリストアップ
            debugger.debug_print("Checkpointファイルをリストアップ")
            self.ckpt_files = [f for f in os.listdir(self.ckpt_dir) if f.endswith('.ckpt') or f.endswith('.safetensors')]

            # チェックポイントが存在しない場合、警告を出して""を返す
            if not self.ckpt_files:
                debugger.debug_print("チェックポイントが見つかりません。")
                return ""

            # チェックポイントが存在する場合、そのファイル名を表示
            for i, filename in enumerate(self.ckpt_files, start=1):
                debugger.debug_print( i, ". ", filename )

            return self.ckpt_files

        except Exception as e:
            debugger.debug_print( "エラーが発生しました: {e}")
            return 0

    def set_checkpoints(self):
        """list_checkpointsを呼び出し、init_checkpointが存在するかチェックし、なければHadrianをダウンロード"""

        # list_checkpointsを呼び出し、インストールされているチェックポイントファイル名を取得
        self.ckpt_files = self.list_checkpoints()

        # チェックポイントが見つからなかった場合、デフォルトチェックポイントをダウンロード
        if not self.ckpt_files:
            print("チェックポイントが見つかりません。Hadrianのチェックポイントをダウンロードします。")

            # 正しいHadrianチェックポイントのダウンロードURL
            self.checkpoint_url = "https://civitai.com/api/download/models/856413?type=Model&format=SafeTensor&size=pruned&fp=fp16"
            self.file_path = os.path.join(self.drive_path, "CheckPoint/hadrianDelicexlPony_v30a2.safetensors")

            # subprocess.Popen を使用して curl コマンドを実行し、進捗バーを表示
            curl_command = [
                "curl", "-L", "-H", f"Authorization: Bearer {self.CivitATI_api_key}", self.checkpoint_url,
                "-o", self.file_path, "--progress-bar"
            ]
            debugger.debug_print( "Executing command: ",' '.join(curl_command) )
            process = subprocess.Popen(curl_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # 標準出力をリアルタイムで読み込んで表示
            for line in process.stdout:
                debugger.debug_print(line, end='')

            process.wait()

            # ダウンロードしたファイルが存在するか確認
            if os.path.exists(self.file_path):
                debugger.debug_print("Hadrianチェックポイントをダウンロードしました: ", self.file_path )
                return "hadrianDelicexlPony_v30a2.safetensors"
        else:
            # init_checkpointがリスト内に存在するかを確認
            if init_checkpoint in self.ckpt_files:
                debugger.debug_print("チェックポイント: ", init_checkpoint, " が見つかりました。設定を続行します。")
                return init_checkpoint
            else:
                # init_checkpointが存在しない場合、ユーザーに選択を促す
                debugger.debug_print("指定されたチェックポイント ", init_checkpoint, " は存在しません。")
                # ユーザーに入力を促す部分は変わらず
                while True:
                    choice = int(input("インストールしたいチェックポイント番号を入力してください: "))
                    if 1 <= choice <= len(self.ckpt_files):
                        self.selected_ckpt = self.ckpt_files[choice - 1]
                        debugger.debug_print( self.selected_ckpt, " が選択されました。")
                        return self.selected_ckpt

# @title ClsDrivePath
class ClsDrivePath:
    def __init__(self, drive_path):
        if drive_path is not None:
            self.drive_path = drive_path
            debugger.debug_print("drive_path :", self.drive_path)
        else:
            debugger.debug_print("drive_path is None")
            sys.exit(0)

    def create_drive_path(self):
        """
        self.drive_path フォルダとその配下に必要なフォルダを作成するメソッド。
        """
        # self.drive_path が存在しない場合は作成
        if not os.path.exists(self.drive_path):
            os.makedirs(self.drive_path, exist_ok=True)
            debugger.debug_print(f"{self.drive_path} フォルダを作成しました。")
        else:
            debugger.debug_print(f"{self.drive_path} フォルダは既に存在します。")

        # 配下に必要なフォルダを作成する
        required_folders = [
            "CheckPoint",
            "extensions",
            "embeddings",
            "Lora",
            "VAE",
            "ControlNet",
            "Config"
        ]

        for folder in required_folders:
            mkdir_path = os.path.join(self.drive_path, folder)
            if not os.path.exists(mkdir_path):
                os.makedirs(mkdir_path, exist_ok=True)
                debugger.debug_print(f"{mkdir_path} フォルダを作成しました。")
            else:
                debugger.debug_print(f"{mkdir_path} フォルダは既に存在します。")

# @title ClsConfig
class ClsConfig:
    def __init__(self, drive_path, repo_folder):
        if drive_path is not None and repo_folder is not None:
            self.drive_path = drive_path
            self.repo_folder = repo_folder
            debugger.debug_print("drive_path :", self.drive_path)
            debugger.debug_print("repo_folder :", self.repo_folder)
            debugger.debug_print("drive_path and repo_folder are not None")
        else:
            debugger.debug_print("drive_path or repo_folder is None")
            sys.exit(0)

    def create_config_files(self):
        """
        必要なファイルをGoogle Colab 側とGoogle Drive 側で同期させるメインメソッド。
        """
        # 同期するファイルとそのデフォルト内容
        files = {
            "config.json": '{\n"quicksettings": "sd_model_checkpoint, sd_vae"\n}\n',  # VAE設定のみ
            "styles.csv": 'Style Name,Prompt,Negative Prompt\n',
            "webui-user.sh": ''  # 空のファイル
        }

        # 各ファイルの同期処理
        self.sync_files(files)

    def sync_files(self, files):
        """
        Google Colab 側と Google Drive 側でファイルを同期させる。
        """
        for filename, default_content in files.items():
            self.sync_file(filename, default_content)

    def sync_file(self, filename, default_content):
        """
        ファイルの同期と生成処理。
        """
        self.drive_side = os.path.join(self.drive_path, "Config", filename)
        self.colab_side = os.path.join(self.repo_folder, filename)

        # Colab 側にファイルが存在しない場合、デフォルトの内容で生成
        if not os.path.exists(self.colab_side):
            with open(self.colab_side, 'w') as f:
                f.write(default_content)
            debugger.debug_print( "Google Colab 側に ", filename, " を生成しました。")

        # Google Drive 側にファイルが存在しない場合、Colab 側からコピー
        if not os.path.exists(drive_path):
            shutil.copy2(self.colab_side, self.drive_side)
            debugger.debug_print( "Google Drive 側に ", filename, " をコピーしました。")

# @title ClsSymlinks
class ClsSymlinks:
    def __init__(self, path_pairs, drive_path, repo_folder):
        if path_pairs is None or drive_path is None or repo_folder is None:
            debugger.debug_print("Initialization parameters are missing.")
            sys.exit(0)
        else:
            debugger.debug_print("Initialization parameters are set.")
            debugger.debug_print("path_pairs: ", path_pairs)
            debugger.debug_print("drive_path: ", drive_path)
            debugger.debug_print("repo_folder: ", repo_folder)

            self.path_pairs = path_pairs
            self.drive_path = drive_path
            self.repo_folder = repo_folder

    def create_symlinks(self):
        debugger.debug_print( "Starting to create symlinks for ", len(self.path_pairs), " pairs")
        for source_suffix, target_suffix in self.path_pairs:
            self.create_symlink_if_needed(
                os.path.join(self.drive_path, source_suffix),
                os.path.join(self.repo_folder, target_suffix)
            )
        debugger.debug_print( "All symlinks created successfully.")

    def create_symlink_if_needed(self, source, target):
        debugger.debug_print( "Attempting to create symlink: ", source, " -> ", target )

        if not os.path.exists(source):
            debugger.debug_print( "Source path does not exist: ", source)
            return

        self.remove_existing_target(target)
        try:
            os.symlink(source, target)
            debugger.debug_print( "Symlink created successfully: ", source, " -> ", target )
        except Exception as e:
            debugger.debug_print( "Failed to create symlink: ", e)

    def remove_existing_target(self, target):
        if os.path.exists(target):
            try:
                if os.path.islink(target):
                    debugger.debug_print( "Removing existing symlink: ", target)
                    os.unlink(target)
                elif os.path.isfile(target):
                    debugger.debug_print( "Removing existing file: ", target )
                    os.remove(target)
                elif os.path.isdir(target):
                    debugger.debug_print( "Removing directory and its contents: ", target )
                    shutil.rmtree(target)
            except Exception as e:
                debugger.debug_print( "Failed to remove existing target: ", e )
        else:
            debugger.debug_print( "Target does not exist: ", target )

"""### 3. StableDiffusionManager起動"""

# @title StableDiffusion起動補助クラスの定義 {"form-width":"400px"}
debugger = initialize_debugger( debug = flg_debug )

class StableDiffusionManager:
    def __init__(self,
                       ckpt_dir='models/Stable-diffusion',
                       ):

        self.repo_folder = repo_folder
        self.repo_url = repo_url
        self.drive_path = drive_path
        self.system_reset = system_reset
        self.checkpoint = None
        self.CivitAI_api_key = CivitAI_api_key
        self.ckpt_dir = os.path.join( self.drive_path, "CheckPoint")
        self.requirements = os.path.join(self.repo_folder, "requirements.txt")          # requirements.txtのフルパス /content/stable-diffusion-webui/requirements.txt

        # Google Drive 側と Colab 側のパスのペアを定義
        self.path_pairs = [
            ['CheckPoint', 'models/Stable-diffusion'],
            ['extensions', 'extensions'],
            ['embeddings', 'embeddings'],
            ['Lora', 'models/Lora'],
            ['VAE', 'models/VAE'],
            ['ControlNet', 'models/ControlNet'],
            ['Config/config.json', 'config.json'],
            ['Config/styles.csv', 'styles.csv'],
            ['Config/webui-user.sh', 'webui-user.sh']
        ]

        self.InsSystemReset = ClsSystemReset( self.system_reset )
        self.InsDrivePath = ClsDrivePath(self.drive_path )
        self.InsRepository = ClsRepository(self.repo_folder )
        self.InsDependencies = ClsDependencies(self.requirements )
        self.InsConfig = ClsConfig( self.drive_path, self.repo_folder )
        self.InsSymlinks = ClsSymlinks(self.path_pairs, self.drive_path, self.repo_folder)
        self.InsCheckpoints = ClsCheckpoints(self.ckpt_dir, self.CivitAI_api_key)

    def setup(self):
        """セットアッププロセスを実行"""
        self.InsSystemReset.reset_drive_if_needed() # Google Driveをリセット
        self.InsDrivePath.create_drive_path()       # サブフォルダを作成する
        self.InsRepository.clone_repository()       # リポジトリをクローン
        self.InsDependencies.install_dependencies() # 依存関係とxformersをインストール
        self.InsConfig.create_config_files()        # 設定ファイルをコピー
        self.InsSymlinks.create_symlinks()          # Google Driveデータをリンク

        # Checkpointの選択
        self.checkpoint = self.InsCheckpoints.set_checkpoints()

    def run(self):
            self.launch_webui()  # WebUIを起動

    def launch_webui(self):
        """Stable Diffusion WebUIを !python でシンプルに起動"""
        print("Launching Stable Diffusion WebUI...")

        # 環境変数を設定して、コンソール出力を少なくする。
        os.environ['WEBUI_LAUNCH_LIVE_OUTPUT'] = '1'

        # 起動コマンドの基本部分をリストで作成
        launch_command = [
            "python", f"{self.repo_folder}/launch.py",  # 正しいパスを指定
            "--listen",
            "--share",  # 他の端末からも共有可能にする
            "--no-half-vae",  # VAE使用時の精度のため
            "--opt-split-attention",  # メモリ最適化
            "--enable-insecure-extension-access",
            "--disable-console-progressbars",  # コンソール出力を減らして軽量化
            "--xformers"  # xformersオプションを追加
        ]

        # チェックポイントが指定されている場合、そのオプションを追加
        if hasattr(self, 'checkpoint') and self.checkpoint:
            launch_command.extend(["--ckpt", os.path.join(self.ckpt_dir, self.checkpoint)])

        # コマンドリストを一つの文字列に結合
        command_str = ' '.join(launch_command)

        # 実行コマンドを表示してから実行
        print(f"Executing: {command_str}")

        # !pythonで実行
        !{command_str}



# StableDiffusionManagerインスタンス作成
stable_diffusion_manager = StableDiffusionManager()

# @title StableDiffusion初期設定
debugger = initialize_debugger( debug = flg_debug )

stable_diffusion_manager.setup()

# @title StableDiffusion起動
stable_diffusion_manager.run()