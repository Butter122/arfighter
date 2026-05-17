using System.Collections;
using UnityEngine;

/// <summary>
/// Lets the user tap on a detected AR plane to place the fighting arena.
/// </summary>
namespace ARFighter.AR
{
    public class ARPlaneSelector : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private ARPlaneManager _planeManager;
        [SerializeField] private ARRaycastManager _raycastManager;
        [SerializeField] private GameObject _arenaPrefab;
        [SerializeField] private GameObject _tapPromptUI;

        private GameObject _spawnedArena;
        private bool _placed = false;

        private void Start()
        {
            _tapPromptUI.SetActive(true);
        }

        private void Update()
        {
            if (_placed || Input.touchCount == 0) return;

            var touch = Input.GetTouch(0);
            if (touch.phase != TouchPhase.Began) return;

            var hits = new System.Collections.Generic.List<ARRaycastHit>();
            if (_raycastManager.Raycast(touch.position, hits,
                UnityEngine.XR.ARSubsystems.TrackableType.PlaneWithinPolygon))
            {
                var hitPose = hits[0].pose;
                _spawnedArena = Instantiate(_arenaPrefab, hitPose.position, hitPose.rotation);
                _placed = true;
                _tapPromptUI.SetActive(false);

                // Hide plane visualizers after placement
                foreach (var plane in _planeManager.trackables)
                    plane.gameObject.SetActive(false);
            }
        }
    }
}
