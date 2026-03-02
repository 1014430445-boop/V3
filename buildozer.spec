[app]
title = 设备监控系统
package.name = mydeviceapp
package.domain = org.example

version = 0.1
version.code = 1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy

# 权限（无需存储权限，数据存私有目录）
android.permissions = INTERNET

# Android 版本
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30

# 如果使用 Kivy 的依赖，可额外添加
# requirements = python3,kivy,plyer,android