using System.Collections;
using UnityEngine;

/// <summary>
/// Controls an AR fighter avatar — animations, positioning, state reactions.
/// </summary>
namespace ARFighter.Game
{
    public class FighterController : MonoBehaviour
    {
        [Header("Settings")]
        [SerializeField] private string _playerId = "p1";
        [SerializeField] private Animator _animator;
        [SerializeField] private float _shakeDuration = 0.2f;
        [SerializeField] private float _shakeIntensity = 0.1f;

        private Vector3 _originalPos;
        private FighterState _currentState;
        private bool _dead = false;

        public string PlayerId => _playerId;

        private void Awake()
        {
            _originalPos = transform.localPosition;
        }

        public void ApplyState(FighterState state)
        {
            if (state == null) return;
            _currentState = state;

            switch (state.state)
            {
                case "hit":
                    OnHit();
                    break;
                case "dead":
                    if (!_dead) OnDead();
                    break;
                case "attacking":
                    OnAttack();
                    break;
                case "blocking":
                    _animator?.SetTrigger("Block");
                    break;
                default:
                    _animator?.SetTrigger("Idle");
                    break;
            }
        }

        private void OnHit()
        {
            _animator?.SetTrigger("Hit");
            EffectSpawner.Instance?.SpawnHitEffect(transform.position + Vector3.up);
            StartCoroutine(ShakeRoutine());
        }

        private void OnAttack()
        {
            _animator?.SetTrigger("Attack");
            // Spawn projectile toward opponent
            var opponent = GameManager.Instance?.GetOpponent(_playerId);
            if (opponent != null)
                EffectSpawner.Instance?.SpawnProjectile(
                    transform.position + Vector3.up,
                    opponent.transform.position + Vector3.up);
        }

        private void OnDead()
        {
            _dead = true;
            _animator?.SetTrigger("Dead");
        }

        private IEnumerator ShakeRoutine()
        {
            float elapsed = 0f;
            while (elapsed < _shakeDuration)
            {
                var offset = Random.insideUnitSphere * _shakeIntensity;
                transform.localPosition = _originalPos + offset;
                elapsed += Time.deltaTime;
                yield return null;
            }
            transform.localPosition = _originalPos;
        }

        public void ResetFighter()
        {
            _dead = false;
            transform.localPosition = _originalPos;
            _animator?.SetTrigger("Idle");
        }
    }
}
