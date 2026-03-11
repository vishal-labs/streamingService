1. We should decide if we wanna use HLS or DASH as the streaming protocol(using HLS)
2. Decided on the endpoints and using helper function for the `<VIDEO>to<HLS>`
3. created input/outputs folders for video storage in the backend folder.
4. **ffmpeg pitfall**: `pip install ffmpeg` installs the wrong package (`ffmpeg` v1.4) which does NOT have `.input()`, `.output()`, `.run()` etc. The correct package is `ffmpeg-python` (`pip install ffmpeg-python`). Installing the wrong one shadows/corrupts the namespace and causes `AttributeError: module 'ffmpeg' has no attribute 'input'`. Fix: `pip uninstall ffmpeg && pip install ffmpeg-python`.
