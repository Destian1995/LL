APP_VERSION="1.8.1"


rm -rf bin && buildozer android clean && git pull && clear && buildozer android release
cd ~/LL/bin
ANDROID_BUILD_TOOLS="$HOME/.buildozer/android/platform/android-sdk/build-tools/36.0.0"

# 1) Zipalign нового мульти-ABI unsigned-APK
$ANDROID_BUILD_TOOLS/zipalign -v -p 4 \
    lerdonlegends-${APP_VERSION}-arm64-v8a_armeabi-v7a-release-unsigned.apk \
    lerdonlegends-${APP_VERSION}-multiabi-release-aligned.apk

# 2) Apksigner нового aligned-APK
$ANDROID_BUILD_TOOLS/apksigner sign \
    --ks ../signkey.keystore \
    --ks-key-alias lerdon-release \
    --ks-pass pass:mypassword \
    --key-pass pass:mypassword \
    --out lerdonlegends-${APP_VERSION}-multiabi-release-signed.apk \
    lerdonlegends-${APP_VERSION}-multiabi-release-aligned.apk

cd ../
cp -rf bin ~/project
ls -l bin
