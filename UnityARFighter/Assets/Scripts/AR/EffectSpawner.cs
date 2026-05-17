using System.Collections;
using UnityEngine;

/// <summary>
/// Spawns and auto-destroys visual effect prefabs at given positions.
/// </summary>
namespace ARFighter.AR
{
    public class EffectSpawner : MonoBehaviour
    {
        [Header("Prefabs")]
        [SerializeField] private GameObject _hitEffectPrefab;
        [SerializeField] private GameObject _projectileEffectPrefab;

        [Header("Settings")]
        [SerializeField] private float _projectileSpeed = 8f;

        public static EffectSpawner Instance { get; private set; }

        private void Awake()
        {
            Instance = this;
        }

        public void SpawnHitEffect(Vector3 position)
        {
            if (_hitEffectPrefab == null) return;
            var go = Instantiate(_hitEffectPrefab, position, Quaternion.identity);
            var ps = go.GetComponent<ParticleSystem>();
            if (ps != null)
                Destroy(go, ps.main.duration);
            else
                Destroy(go, 1.5f);
        }

        public void SpawnProjectile(Vector3 from, Vector3 to)
        {
            if (_projectileEffectPrefab == null) return;
            StartCoroutine(AnimateProjectile(from, to));
        }

        private IEnumerator AnimateProjectile(Vector3 from, Vector3 to)
        {
            var go = Instantiate(_projectileEffectPrefab, from, Quaternion.identity);
            float t = 0f;
            float duration = Vector3.Distance(from, to) / _projectileSpeed;

            while (t < duration)
            {
                t += Time.deltaTime;
                if (go != null)
                    go.transform.position = Vector3.Lerp(from, to, t / duration);
                yield return null;
            }

            if (go != null)
            {
                SpawnHitEffect(to);
                Destroy(go);
            }
        }
    }
}
