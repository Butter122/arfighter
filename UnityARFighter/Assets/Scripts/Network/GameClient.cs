using System;
using System.Collections;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using ARFighter.Game;

/// <summary>
/// WebSocket client using only built-in .NET APIs (no external packages).
/// Connects to the game server for real-time state and to the inference
/// service for frame uploads.
/// </summary>
namespace ARFighter.Network
{
    public class GameClient : MonoBehaviour
    {
        [Header("Servers")]
        [SerializeField] private string _serverIP = "192.168.1.100";

        // Events
        public event Action<ServerMessage> OnStateUpdated;
        public event Action<string> OnConnected;
        public event Action<string> OnDisconnected;

        // State
        public string PlayerId { get; private set; }
        public bool IsConnected { get; private set; }

        private ClientWebSocket _ws;
        private CancellationTokenSource _cts;
        private string _gameServerUrl => $"ws://{_serverIP}:8000/ws";
        private string _inferenceUrl => $"http://{_serverIP}:8001/frame";

        private void Start()
        {
            _ = ConnectLoopAsync();
        }

        private void OnDestroy()
        {
            Disconnect();
        }

        // ---- Game Server WebSocket (built-in System.Net.WebSockets) ----

        private async Task ConnectLoopAsync()
        {
            while (this != null)
            {
                try
                {
                    _cts = new CancellationTokenSource();
                    _ws = new ClientWebSocket();
                    await _ws.ConnectAsync(new Uri(_gameServerUrl), _cts.Token);

                    IsConnected = true;
                    Debug.Log("[GameClient] Connected to game server");

                    // Read loop (runs on thread pool, dispatches to main thread)
                    await ReceiveLoopAsync(_cts.Token);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[GameClient] Connection failed: {ex.Message}");
                }
                finally
                {
                    IsConnected = false;
                    _ws?.Dispose();
                    _ws = null;
                }

                OnDisconnected?.Invoke("Reconnecting...");
                await Task.Delay(3000, CancellationToken.None);
            }
        }

        private async Task ReceiveLoopAsync(CancellationToken ct)
        {
            var buffer = new byte[4096];

            while (_ws?.State == WebSocketState.Open && !ct.IsCancellationRequested)
            {
                var result = await _ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                if (result.MessageType == WebSocketMessageType.Close)
                    break;

                var json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                Debug.Log($"[GameClient] Received: {json}");

                // Dispatch to main thread
                UnityMainThreadDispatcher.Instance?.Enqueue(() => ProcessMessage(json));
            }
        }

        private void ProcessMessage(string json)
        {
            if (json.Contains("\"type\":\"welcome\""))
            {
                var welcome = JsonUtility.FromJson<WelcomeMessage>(json);
                PlayerId = welcome.player_id;
                OnConnected?.Invoke(PlayerId);
                return;
            }

            var state = JsonUtility.FromJson<ServerMessage>(json);
            OnStateUpdated?.Invoke(state);
        }

        public void Disconnect()
        {
            _cts?.Cancel();
            _ws?.Dispose();
            _ws = null;
            IsConnected = false;
        }

        // ---- HTTP: Send frame to inference service ----

        public IEnumerator SendFrame(byte[] jpegBytes, string playerId)
        {
            var url = $"{_inferenceUrl}/{playerId}";

            using var req = new UnityWebRequest(url, "POST");
            req.uploadHandler = new UploadHandlerRaw(jpegBytes);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/octet-stream");

            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                var response = req.downloadHandler.text;
                if (response.Contains("\"action\":null")) yield break;

                var result = JsonUtility.FromJson<InferenceResponse>(response);
                if (!string.IsNullOrEmpty(result.action))
                    _ = SendActionToGameServer(playerId, result.action);
            }
        }

        // ---- Send action to game server ----

        public async Task SendActionToGameServer(string playerId, string action)
        {
            if (_ws?.State != WebSocketState.Open) return;

            var json = JsonUtility.ToJson(new PlayerAction
            {
                player_id = playerId,
                action = action
            });

            var bytes = Encoding.UTF8.GetBytes(json);
            try
            {
                await _ws.SendAsync(
                    new ArraySegment<byte>(bytes),
                    WebSocketMessageType.Text,
                    true,
                    CancellationToken.None);
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[GameClient] Send failed: {ex.Message}");
            }
        }

        public void SendAction(string action)
        {
            if (!string.IsNullOrEmpty(PlayerId))
                _ = SendActionToGameServer(PlayerId, action);
        }
    }

    /// <summary>
    /// Singleton to dispatch callbacks onto Unity's main thread.
    /// Attach to a GameObject in your scene (e.g., on the GameManager object).
    /// </summary>
    public class UnityMainThreadDispatcher : MonoBehaviour
    {
        public static UnityMainThreadDispatcher Instance { get; private set; }

        private readonly System.Collections.Generic.Queue<Action> _queue =
            new System.Collections.Generic.Queue<Action>();

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Update()
        {
            lock (_queue)
            {
                while (_queue.Count > 0)
                    _queue.Dequeue()?.Invoke();
            }
        }

        public void Enqueue(Action action)
        {
            lock (_queue) { _queue.Enqueue(action); }
        }
    }
}
