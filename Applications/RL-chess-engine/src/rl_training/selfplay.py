"""Self-play training for chess engines."""

import numpy as np
from typing import Tuple, Optional, Dict, List
import logging
from pathlib import Path
from multiprocessing import Pool
import os
from src.rl_training import Experience
from src.models.encoder import BoardEncoder


def _play_game_worker(args: Tuple) -> Tuple[float, int, list, list]:
    """
    Worker function for parallel game generation.
    Plays a single game and returns result and experiences.
    
    Args:
        args: Tuple of (agent, opponent, game_class, training, max_moves)
        
    Returns:
        Tuple of (result, move_count, agent1_experiences, agent2_experiences)
    """
    agent, opponent, game_class, training, max_moves = args
    sp_game = SelfPlayGame(agent, opponent, game_class, max_moves=max_moves)
    result, move_count, exp_agent1, exp_agent2 = sp_game.play(training=training)
    return result, move_count, exp_agent1, exp_agent2
from src.chess_engine.board import Square


class SelfPlayGame:
    """Self-play game between two agents."""
    
    def __init__(self, agent1, agent2, game_class, max_moves: int = 200):
        """
        Initialize self-play game.
        
        Args:
            agent1: First agent (white)
            agent2: Second agent (black)
            game_class: ChessGame class for creating games
            max_moves: Maximum moves before draw
        """
        self.agent1 = agent1
        self.agent2 = agent2
        self.game_class = game_class
        self.max_moves = max_moves
        self.move_history = []
    
    def play(self, training: bool = True) -> Tuple[float, int, list, list]:
        """
        Play a complete game.
        
        Args:
            training: Whether agents are in training mode
            
        Returns:
            Tuple of (result, move_count, agent1_experiences, agent2_experiences)
        """
        game = self.game_class()
        self.move_history = []
        game_transitions = []  # Store transitions for replay buffer
        
        while not game.is_game_over() and len(game.board.move_history) < self.max_moves:
            current_agent = self.agent1 if game.board.current_player.value == 0 else self.agent2
            
            # Get legal moves
            legal_moves_tuples = game.get_legal_moves()
            legal_moves_mask = np.zeros(4096, dtype=bool)
            for from_sq, to_sq in legal_moves_tuples:
                from_idx = from_sq.to_index()
                to_idx = to_sq.to_index()
                move_idx = from_idx * 64 + to_idx
                legal_moves_mask[move_idx] = True
            
            # Get action
            state = game.board.get_board_state()
            action = current_agent.get_action(state, legal_moves_mask, training=training)
            
            # Convert action to move
            from_idx, to_idx = divmod(action, 64)
            from_row, from_col = from_idx // 8, from_idx % 8
            to_row, to_col = to_idx // 8, to_idx % 8
            
            # Make move
            from_sq_obj = Square(from_row, from_col)
            to_sq_obj = Square(to_row, to_col)
            game.make_move(from_sq_obj, to_sq_obj)
            
            # Store transition for replay buffer (encode state to 12 planes)
            next_state = game.board.get_board_state()
            encoded_state = BoardEncoder.encode_planes(state)
            encoded_next_state = BoardEncoder.encode_planes(next_state)
            game_transitions.append((encoded_state, action, legal_moves_mask, encoded_next_state))
            
            self.move_history.append(action)
        
        # Determine result
        if game.is_game_over():
            result = game.get_result()
            if result.value == 1:  # White wins
                final_result = -1.0
            elif result.value == -1:  # Black wins
                final_result = 1.0
            else:  # Draw
                final_result = 0.0
        else:
            final_result = 0.0  # Max moves reached, draw
        
        # Create experiences (but don't store them - return them instead)
        agent1_experiences = []
        agent2_experiences = []
        
        for state, action, legal_moves_mask, next_state in game_transitions:
            reward = final_result
            done = False
            
            # Both agents learn from the same game with opposite rewards
            exp_agent1 = Experience(state=state, action=action, reward=reward, 
                                   next_state=next_state, done=done, legal_moves=legal_moves_mask)
            exp_agent2 = Experience(state=state, action=action, reward=-reward,
                                   next_state=next_state, done=done, legal_moves=legal_moves_mask)
            
            agent1_experiences.append(exp_agent1)
            agent2_experiences.append(exp_agent2)
        
        return final_result, len(game.board.move_history), agent1_experiences, agent2_experiences


class SelfPlayTrainer:
    """Trainer using self-play."""
    
    def __init__(self, agent, game_class, log_dir: Optional[str] = None, max_moves_per_game: int = 100):
        """
        Initialize self-play trainer.
        
        Args:
            agent: Agent to train
            game_class: ChessGame class
            log_dir: Directory for logs
            max_moves_per_game: Maximum moves per game
        """
        self.agent = agent
        self.game_class = game_class
        self.log_dir = Path(log_dir) if log_dir else None
        self.max_moves_per_game = max_moves_per_game
        
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.training_history = []
    
    def train_epoch(self, num_games: int = 100, batch_size: int = 32, training_iterations: int = 1, num_workers: int = 10) -> Dict[str, float]:
        """
        Run training epoch with parallel self-play.
        
        Args:
            num_games: Number of games to play
            batch_size: Batch size for training
            training_iterations: Training iterations per epoch
            num_workers: Number of parallel workers for game generation
            
        Returns:
            Statistics dictionary
        """
        results = {'white_wins': 0, 'black_wins': 0, 'draws': 0, 'total_moves': 0}
        
        # Play games in parallel using multiprocessing
        self.logger.info(f"Playing {num_games} games with {num_workers} workers...")
        
        with Pool(processes=num_workers) as pool:
            # Create arguments for each game (including max_moves)
            game_args = [(self.agent, self.agent, self.game_class, True, self.max_moves_per_game) for _ in range(num_games)]
            
            # Map games across workers
            game_results = pool.map_async(
                _play_game_worker,
                game_args
            ).get()
        
        # Process results and collect experiences
        for result, move_count, exp_agent1, exp_agent2 in game_results:
            if result < 0:
                results['white_wins'] += 1
            elif result > 0:
                results['black_wins'] += 1
            else:
                results['draws'] += 1
            
            results['total_moves'] += move_count
            
            # Store experiences returned from workers in main process agent
            for exp in exp_agent1:
                self.agent.store_experience(exp)
            for exp in exp_agent2:
                self.agent.store_experience(exp)
        
        # Train on all collected game data after all games
        epoch_value_losses = []
        epoch_policy_losses = []
        for iteration in range(training_iterations):
            value_loss, policy_loss = self.agent.train(batch_size=batch_size)
            epoch_value_losses.append(value_loss)
            epoch_policy_losses.append(policy_loss)
        
        # Decay epsilon
        self.agent.epsilon = max(self.agent.epsilon_min, 
                                 self.agent.epsilon * self.agent.epsilon_decay)
        
        # Compute averages
        stats = {
            'white_win_rate': results['white_wins'] / num_games,
            'black_win_rate': results['black_wins'] / num_games,
            'draw_rate': results['draws'] / num_games,
            'avg_moves': results['total_moves'] / num_games,
            'value_loss': sum(epoch_value_losses) / len(epoch_value_losses) if epoch_value_losses else 0.0,
            'policy_loss': sum(epoch_policy_losses) / len(epoch_policy_losses) if epoch_policy_losses else 0.0,
        }
        
        self.training_history.append(stats)
        return stats
