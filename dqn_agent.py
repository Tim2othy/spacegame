import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Tuple
from pygame.math import Vector2 as Vec2


class DQN(nn.Module):
    def __init__(self, input_size: int, output_size: int):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)


class DQNAgent:
    def __init__(
        self,
        state_size: int,
        action_size: int,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99,
        exploration_rate: float = 1.0,
        exploration_decay: float = 0.995,
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_min = 0.01
        self.exploration_decay = exploration_decay

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQN(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()

    def get_action(self, state: np.ndarray) -> int:
        if np.random.rand() < self.exploration_rate:
            return np.random.randint(self.action_size)

        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return q_values.argmax().item()

    def train(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
        action_tensor = torch.LongTensor([action]).to(self.device)
        reward_tensor = torch.FloatTensor([reward]).to(self.device)
        done_tensor = torch.FloatTensor([done]).to(self.device)

        q_values = self.model(state_tensor)
        next_q_values = self.model(next_state_tensor)

        q_value = q_values.gather(1, action_tensor.unsqueeze(1)).squeeze(1)
        next_q_value = next_q_values.max(1)[0]
        expected_q_value = reward_tensor + self.discount_factor * next_q_value * (
            1 - done_tensor
        )

        loss = self.criterion(q_value, expected_q_value.detach())

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.exploration_rate = max(
            self.exploration_min, self.exploration_rate * self.exploration_decay
        )


def get_state(
    enemy_pos: Vec2,
    enemy_vel: Vec2,
    enemy_angle: float,
    player_pos: Vec2,
    player_vel: Vec2,
) -> np.ndarray:
    relative_pos = player_pos - enemy_pos
    relative_vel = player_vel - enemy_vel

    return np.array(
        [
            relative_pos.x,
            relative_pos.y,
            relative_vel.x,
            relative_vel.y,
            enemy_angle,
            enemy_vel.x,
            enemy_vel.y,
        ]
    )
