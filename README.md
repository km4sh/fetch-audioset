# fetch-audioset

下載AudioSet主要用的是下載神器`youtube-dl`來實現的。可以[點擊這裏](https://github.com/km4sh/fetch-audioset/blob/development/scripts/download_audioset.py)直達。由於接口原因，貌似沒有可以直接下載音頻的方式，所以需要先下載視頻，再提取音頻。所以主要流程如下：

- `split_samplename()` 將輸入參數處理爲視頻ID `ytid` 和開始時間 `start` ；
- `download_video()` 利用ytid將整段視頻下載下來；
- `convert_to_audio()` 利用FFmpeg將視頻中的音頻提取出來，順便完成通道壓縮（僅單通道）、採樣率調整（統一44100Hz）以及格式轉換（WAV）等任務。
- `trim_audio()` 利用sox工具進行音頻剪切。
    - 這裏需要說明的是，雖然FFmpeg也可以一同完成剪切任務，單我在之前的下載當中，發現一些利用FFmpeg剪切後的文件長度並不是嚴格的`SampleRate * Duration`個樣點。後來發現部分AudioSet的樣本可能不足十秒，原因是原視頻就不足十秒。不過我也不確定FFmpeg剪切是完全魯棒的，所以我用了更保險的sox工具來進行剪切。
- `padding_zeros()` 如上一步的說明，如果有一些樣本不足十秒，則補零到十秒。這一步可以根據自己的需求選用。
- `checking()` 檢查當前文件是否符合要求，主要檢查通道數、採樣率、採樣深度、採樣時間、總樣點數。也是利用sox來獲取的文檔信息，確保準確可讀。

對於下載當中由於網絡等原因出現下載失敗的情況，我們可以用`[clean.py](https://github.com/km4sh/fetch-audioset/blob/development/scripts/clean.py)`來清理一下臨時文件，以及不符合我們設定格式的文件。
