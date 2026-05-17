using UnityEngine;
using ARFighter.Network;
using ARFighter.UI;
using ARFighter.Game;

/// <summary>
/// Central controller — wires WebSocket events to fighters and HUD.
/// </summary>
namespace ARFighter.Game
{
    public class GameManager : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private GameClient _gameClient;
        [SerializeField] private HUDManager _hud;
        [SerializeField] private FighterController _p1Fighter;
        [SerializeField] private FighterController _p2Fighter;

        public static GameManager Instance { get; private set; }

        private bool _roundOver = false;

        private void Awake()
        {
            Instance = this;
        }

        private void OnEnable()
        {
            if (_gameClient == null) return;
            _gameClient.OnConnected += HandleConnected;
            _gameClient.OnDisconnected += HandleDisconnected;
            _gameClient.OnStateUpdated += HandleStateUpdated;
        }

        private void OnDisable()
        {
            if (_gameClient == null) return;
            _gameClient.OnConnected -= HandleConnected;
            _gameClient.OnDisconnected -= HandleDisconnected;
            _gameClient.OnStateUpdated -= HandleStateUpdated;
        }

        private void HandleConnected(string playerId)
        {
            _hud?.OnConnected();
        }

        private void HandleDisconnected(string reason)
        {
            _hud?.OnDisconnected();
        }

        private void HandleStateUpdated(ServerMessage state)
        {
            if (_roundOver) return;

            _hud?.UpdateHealth(state);

            // Update fighter animations
            if (_p1Fighter != null && state.p1 != null)
                _p1Fighter.ApplyState(state.p1);
            if (_p2Fighter != null && state.p2 != null)
                _p2Fighter.ApplyState(state.p2);

            // Check winner
            if (!string.IsNullOrEmpty(state.winner))
            {
                _roundOver = true;
                _hud?.ShowWinner(state.winner);
                Invoke(nameof(ResetRound), 3f);
            }
        }

        private void ResetRound()
        {
            _roundOver = false;
            _p1Fighter?.ResetFighter();
            _p2Fighter?.ResetFighter();
        }

        public FighterController GetOpponent(string playerId)
        {
            if (playerId == "p1") return _p2Fighter;
            if (playerId == "p2") return _p1Fighter;
            return null;
        }
    }
}
