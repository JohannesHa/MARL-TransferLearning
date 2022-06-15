
from torch.nn import Module
import torch
import torch.nn as nn

class EmbeddingCritic(Module):
    def __init__(self, observation_length=18, action_length=18, embedding_dim=8) -> None:
        super().__init__()
        self.observation_embedding = torch.nn.EmbeddingBag(observation_length, embedding_dim, sparse=True, mode='mean')
        self.action_embedding = torch.nn.Embedding(action_length, embedding_dim, sparse=True)
        self.linear = nn.Linear(2*embedding_dim, 1)
        self.action_length = action_length

        self.observation_length = observation_length
        self.action_length = action_length
        self.embedding_dim = embedding_dim

    def forward(self, observation: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """
        observation: (batch_size, component_size)
        actions: (batch_size, component_size)
        """
        # one hot encode actions
        # 1 0 0
        # 0 1 0
        # 0 0 1

        # actor:
        # 0.1 0.9. 0.0
        # |
        # index vom max:
        # 1
        # |
        # index vom max in identity matrix:
        # 0 1 0
        # TODO: Braucht das embedding die one hot encoding vektoren oder die indizes von 1 stellen?
        actions = torch.eye(self.action_length)[actions.argmax(dim=1)]
        # embed observations
        encoded_observations = self.observation_embedding(observation)
        # embed actions
        encoded_actions= self.action_embedding(actions)
        # concatenate the two embeddings
        concatenated = torch.cat([encoded_observations, encoded_actions], dim=1)
        # pass through the linear layer
        return self.linear(concatenated)
        
    def clone(self):
        return EmbeddingCritic(self.observation_length, self.action_length, self.embedding_dim)


class WeightedEmbeddingCritic(Module):
    def __init__(self, observation_length=18, action_length=18, embedding_dim=8) -> None:
        super().__init__()
        self.observation_length = observation_length
        self.action_length = action_length
        self.embedding_dim = embedding_dim
        self.observation_embedding = torch.nn.EmbeddingBag(observation_length, embedding_dim, sparse=True, mode='mean')
        # Use probability of action for weighted mean of embeddings
        self.action_embedding = torch.nn.Embedding(action_length, embedding_dim, sparse=True)
        self.one_hot = torch.eye(action_length)
        self.linear = nn.Linear(2*embedding_dim, 1)

    def forward(self, observation: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """
        observation: (batch_size, component_size)
        actions_probs: (batch_size, component_size)
        """
        # use weighted mean of embedding outputs
        action_embedding_weight = self.action_embedding(self.one_hot)
        action_embedding_weight *= actions
        action_embedding_weight = action_embedding_weight.sum(dim=1)
        action_embedding_weight /= actions.size(1)
        # embed observations
        encoded_observations = self.observation_embedding(observation)
        # concatenate the two embeddings
        concatenated = torch.cat([encoded_observations, action_embedding_weight], dim=1)
        # pass through the linear layer
        return self.linear(concatenated)
    
    def clone(self):
        return WeightedEmbeddingCritic(self.observation_length, self.action_length, self.embedding_dim)

class LinearConcatCritic(Module):
    def __init__(self, observation_length=270, action_length=18) -> None:
        super().__init__()
        self.observation_length = observation_length
        self.action_length = action_length
        self.linear = nn.Linear(observation_length + action_length, 1)

    def forward(self, observation: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """
        observation: (batch_size, components)
        actions: (batch_size, components)
        """
        cat_dim = 0 if observation.dim() == 1 else 1
        return self.linear(torch.cat((observation, actions), dim=cat_dim))

    def clone(self):
        return LinearConcatCritic(self.observation_length, self.action_length)