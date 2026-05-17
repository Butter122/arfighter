using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Manages health bars, winner announcement, and connection status UI.
/// Health bars animate smoothly using Lerp.
/// </summary>
namespace ARFighter.UI
{
    public class HUDManager : MonoBehaviour
    {
        [Header("Health Bars")]
        [SerializeField] private Slider _p1HealthBar;
        [SerializeField] private Slider _p2HealthBar;
        [SerializeField] private float _healthLerpSpeed = 3.3f; // completes in ~0.3s

        [Header("Winner UI")]
        [SerializeField] private GameObject _winnerPanel;
        [SerializeField] private TMP_Text _winnerText;

        [Header("Connection")]
        [SerializeField] private GameObject _connectingOverlay;

        private float _p1TargetHp, _p2TargetHp;

        private void Start()
        {
            _connectingOverlay?.SetActive(true);
            _winnerPanel?.SetActive(false);

            _p1TargetHp = _p1HealthBar != null ? _p1HealthBar.maxValue : 1f;
            _p2TargetHp = _p2HealthBar != null ? _p2HealthBar.maxValue : 1f;
        }

        public void OnConnected()
        {
            _connectingOverlay?.SetActive(false);
        }

        public void OnDisconnected()
        {
            _connectingOverlay?.SetActive(true);
        }

        public void UpdateHealth(ARFighter.Game.ServerMessage state)
        {
            if (state.p1 != null)
                _p1TargetHp = _p1HealthBar != null
                    ? (float)state.p1.hp / state.p1.max_hp
                    : 1f;
            if (state.p2 != null)
                _p2TargetHp = _p2HealthBar != null
                    ? (float)state.p2.hp / state.p2.max_hp
                    : 1f;
        }

        private void Update()
        {
            if (_p1HealthBar != null)
                _p1HealthBar.value = Mathf.Lerp(
                    _p1HealthBar.value, _p1TargetHp, Time.deltaTime * _healthLerpSpeed);
            if (_p2HealthBar != null)
                _p2HealthBar.value = Mathf.Lerp(
                    _p2HealthBar.value, _p2TargetHp, Time.deltaTime * _healthLerpSpeed);
        }

        public void ShowWinner(string winnerId)
        {
            _winnerPanel?.SetActive(true);
            if (_winnerText != null)
            {
                if (winnerId == "draw")
                    _winnerText.text = "DRAW!";
                else
                    _winnerText.text = $"{winnerId.ToUpper()} WINS!";
            }
            StartCoroutine(HideWinnerAfterDelay(3f));
        }

        private IEnumerator HideWinnerAfterDelay(float delay)
        {
            yield return new WaitForSeconds(delay);
            _winnerPanel?.SetActive(false);
        }
    }
}
