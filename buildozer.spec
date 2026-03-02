[app]
title = DeviceMonitor
package.name = devicecounter
package.domain = org.example
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
requirements = python3,kivy==2.2.1,Cython==0.29.36,plyer==2.1
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 29
android.minapi = 21
android.ndk = 25b
android.sdk = 29
android.accept_sdk_license = True

# 建议让 buildozer 自动选择最新的 build-tools，删除该行或设为一个较高的版本
# android.build_tools_version = 33.0.2

android.arch = arm64-v8a

# 移除冲突的版本设置
# android.gradle = 1               # 不是标准选项，可删除
# android.gradle_version = 4.2.2    # 冲突项，必须删除
android.gradle_options = --stacktrace --info
android.gradle_plugin_version = 8.0.2    # ✅ 使用与 Gradle 8.0.2 兼容的 AGP 8.0.2

# 建议启用 AndroidX，与命令行 --enable-androidx 保持一致
android.use_androidx = True

android.debug = True
android.entrypoint = org.kivy.android.PythonActivity
android.app_lib_dir = %(source.dir)s/libs
android.add_src =
android.enable_ads = 0
android.google_play_services = 0
android.allow_backup = 1
android.theme = @android:style/Theme.NoTitleBar
android.orientation = landscape
android.fullscreen = 0
android.log_level = 2
window.size = 1200x800
osx.python_version = 3
osx.kivy_version = 2.2.1

[buildozer]
log_level = 2
warn_on_root = 1
