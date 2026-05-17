using System;
using UnityEngine;

/// <summary>
/// Serializable data models matching the server JSON.
/// </summary>
namespace ARFighter.Game
{
    [Serializable]
    public class FighterState
    {
        public string player_id;
        public int hp;
        public int max_hp;
        public string state;
    }

    [Serializable]
    public class ServerMessage
    {
        public FighterState p1;
        public FighterState p2;
        public string winner;
        public int tick;
    }

    [Serializable]
    public class WelcomeMessage
    {
        public string type;
        public string player_id;
    }

    [Serializable]
    public class PlayerAction
    {
        public string player_id;
        public string action;
    }

    [Serializable]
    public class InferenceResponse
    {
        public string action;
        public float confidence;
    }
}
