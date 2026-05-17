## Unity Integration Notes

### Sending frames

Unity should POST JPEG frames to the inference service:

```
POST http://<SERVER_IP>:8001/frame/p1   (player 1)
POST http://<SERVER_IP>:8001/frame/p2   (player 2)
```

The body is raw JPEG bytes (use `UnityWebRequest` with `UploadHandlerRaw`).

### Recommended settings

- Send **every 3rd frame** to reduce bandwidth (~10 FPS).
- JPEG quality 50-70% is sufficient for MediaPipe.
- Resolution: 320×240 or 480×360 (lower = faster inference).

### Example Unity code (coroutine)

```csharp
IEnumerator SendFrame(byte[] jpegBytes, string playerId)
{
    using var req = new UnityWebRequest(
        $"http://{serverIp}:8001/frame/{playerId}", "POST");
    req.uploadHandler = new UploadHandlerRaw(jpegBytes);
    req.downloadHandler = new DownloadHandlerBuffer();
    req.SetRequestHeader("Content-Type", "application/octet-stream");
    yield return req.SendWebRequest();

    if (req.result == UnityWebRequest.Result.Success)
    {
        var json = JsonUtility.FromJson<InferenceResponse>(req.downloadHandler.text);
        // json.action, json.confidence
    }
}

[Serializable]
class InferenceResponse { public string action; public float confidence; }
```

### Health check

```
GET http://<SERVER_IP>:8001/health
```
