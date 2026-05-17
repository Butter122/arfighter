using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using ARFighter.Game;

/// <summary>
/// WebSocket client that connects to the inference service and game server.
/// Uses UnityWebRequest for HTTP POST (frame upload) and a WebSocket library
/// for real-time game state.
///
/// Recommended WebSocket asset: NativeWebSocket (open source, GitHub)
/// Install via UPM: https://github.com/endel/NativeWebSocket.git#upm
/// </summary>
namespace ARFighter.Network
{
    public class GameClient : MonoBehaviour
    {
        [Header("Servers")]
        [SerializeField] private string _inferenceServerIP = "192.168.1.100";
        [SerializeField] private int _inferencePort = 8001;

        // Events
        public event Action<ServerMessage> OnStateUpdated;
        public event Action<string> OnConnected;
        public event Action<string> OnDisconnected;
        public event Action<InferenceResponse> OnInferenceResult;

        // State
        public string PlayerId { get; private set; }
        public bool IsConnected { get; private set; }

        private WebSocket _gameWs;
        private string _gameServerUrl => $"ws://{_inferenceServerIP}:8000/ws";
        private bool _shouldReconnect = true;

        private void Start()
        {
            StartCoroutine(ConnectToGameServer());
        }

        private void OnDestroy()
        {
            _shouldReconnect = false;
            _gameWs?.Close();
        }

        // ---- Game Server WebSocket ----

        private IEnumerator ConnectToGameServer()
        {
            // Wait a frame for NativeWebSocket setup, then create
            yield return null;

            _gameWs = new WebSocket(_gameServerUrl);

            _gameWs.OnOpen += () =>
            {
                IsConnected = true;
                Debug.Log($"[GameClient] Connected to game server");
            };

            _gameWs.OnMessage += (bytes) =>
            {
                var json = System.Text.Encoding.UTF8.GetString(bytes);
                Debug.Log($"[GameClient] Received: {json}");

                // Check for welcome message
                if (json.Contains("\"type\":\"welcome\""))
                {
                    var welcome = JsonUtility.FromJson<WelcomeMessage>(json);
                    PlayerId = welcome.player_id;
                    OnConnected?.Invoke(PlayerId);
                    return;
                }

                // Parse as game state
                var state = JsonUtility.FromJson<ServerMessage>(json);
                UnityMainThreadDispatcher.Instance.Enqueue(() =>
                {
                    OnStateUpdated?.Invoke(state);
                });
            };

            _gameWs.OnError += (err) =>
            {
                Debug.LogError($"[GameClient] WebSocket error: {err}");
            };

            _gameWs.OnClose += (code) =>
            {
                IsConnected = false;
                OnDisconnected?.Invoke($"Closed: {code}");
                if (_shouldReconnect)
                    StartCoroutine(ReconnectRoutine());
            };

            _gameWs.Connect();
        }

        private IEnumerator ReconnectRoutine()
        {
            yield return new WaitForSeconds(3f);
            if (_shouldReconnect)
                StartCoroutine(ConnectToGameServer());
        }

        // ---- HTTP: Send frame to inference service ----

        public IEnumerator SendFrame(byte[] jpegBytes, string playerId)
        {
            var url = $"http://{_inferenceServerIP}:{_inferencePort}/frame/{playerId}";

            using var req = new UnityWebRequest(url, "POST");
            req.uploadHandler = new UploadHandlerRaw(jpegBytes);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/octet-stream");

            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                var result = JsonUtility.FromJson<InferenceResponse>(
                    req.downloadHandler.text);
                if (result.action != null)
                {
                    OnInferenceResult?.Invoke(result);
                    SendActionToGameServer(playerId, result.action);
                }
            }
            else
            {
                Debug.LogWarning($"[GameClient] Frame upload failed: {req.error}");
            }
        }

        // ---- WebSocket: Send action to game server ----

        public void SendActionToGameServer(string playerId, string action)
        {
            if (_gameWs == null || !IsConnected) return;

            var msg = new PlayerAction { player_id = playerId, action = action };
            var json = JsonUtility.ToJson(msg);
            _gameWs.SendText(json);
        }

        public void SendAction(string action)
        {
            if (!string.IsNullOrEmpty(PlayerId))
                SendActionToGameServer(PlayerId, action);
        }
    }

    /// <summary>
    /// Minimal singleton to dispatch callbacks onto Unity's main thread.
    /// Attach to a GameObject in your scene.
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
