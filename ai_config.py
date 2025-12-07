# ai_config.py

AI_CONFIG = {
    'use_neural_ai': True,           # Включить нейро-ИИ
    'model_path': 'models/tinyllama.q4.gguf',
    'max_response_time': 3.0,

    # Настройки дипломатии
    'diplomacy': {
        'player_behavior_analysis': True,
        'war_decision_threshold': 0.5,
        'min_friendliness_for_peace': 50,
        'max_aggression_for_war': 70,
        'consider_history_depth': 10  # Количество последних взаимодействий для анализа
    },

    # Настройки личности
    'personality_weights': {
        'relation_weight': 0.4,
        'strength_weight': 0.3,
        'behavior_weight': 0.2,
        'history_weight': 0.1
    }
}