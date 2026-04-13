''' Train a DQN or NFSP agent on Scopa using RLCard '''
import os
import argparse

import torch

import rlcard
from rlcard.agents import RandomAgent
from rlcard.utils import (
    get_device,
    set_seed,
    tournament,
    reorganize,
    Logger,
    plot_curve,
)


def train(args):
    device = get_device()
    set_seed(args.seed)

    env = rlcard.make('scopa', config={'seed': args.seed})
    eval_env = rlcard.make('scopa', config={'seed': args.seed + 1})

    if args.algorithm == 'dqn':
        from rlcard.agents import DQNAgent
        if args.load_checkpoint_path:
            agent = DQNAgent.from_checkpoint(checkpoint=torch.load(args.load_checkpoint_path))
        else:
            agent = DQNAgent(
                num_actions=env.num_actions,           # 40
                state_shape=env.state_shape[0],        # [163]
                mlp_layers=[256, 256],
                replay_memory_size=50000,
                replay_memory_init_size=500,
                epsilon_decay_steps=50000,
                device=device,
                save_path=args.log_dir,
                save_every=args.save_every,
            )

    elif args.algorithm == 'nfsp':
        from rlcard.agents import NFSPAgent
        if args.load_checkpoint_path:
            agent = NFSPAgent.from_checkpoint(checkpoint=torch.load(args.load_checkpoint_path))
        else:
            agent = NFSPAgent(
                num_actions=env.num_actions,
                state_shape=env.state_shape[0],
                hidden_layers_sizes=[256, 256],
                q_mlp_layers=[256, 256],
                device=device,
                save_path=args.log_dir,
                save_every=args.save_every,
            )

    opponents = [RandomAgent(num_actions=env.num_actions) for _ in range(env.num_players - 1)]
    env.set_agents([agent] + opponents)
    eval_env.set_agents([agent] + [RandomAgent(num_actions=eval_env.num_actions) for _ in range(eval_env.num_players - 1)])

    with Logger(args.log_dir) as logger:
        for episode in range(args.num_episodes):
            if args.algorithm == 'nfsp':
                agent.sample_episode_policy()

            trajectories, payoffs = env.run(is_training=True)
            trajectories = reorganize(trajectories, payoffs)

            for ts in trajectories[0]:
                agent.feed(ts)

            if episode % args.evaluate_every == 0:
                logger.log_performance(
                    episode,
                    tournament(eval_env, args.num_eval_games)[0],
                )

        csv_path, fig_path = logger.csv_path, logger.fig_path

    try:
        plot_curve(csv_path, fig_path, args.algorithm)
    except ModuleNotFoundError:
        print('matplotlib not installed — skipping learning curve plot')

    save_path = os.path.join(args.log_dir, 'model.pth')
    torch.save(agent, save_path)
    print('Model saved in', save_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Train DQN/NFSP on Scopa')
    parser.add_argument('--algorithm', type=str, default='dqn', choices=['dqn', 'nfsp'])
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num_episodes', type=int, default=10000)
    parser.add_argument('--num_eval_games', type=int, default=2000)
    parser.add_argument('--evaluate_every', type=int, default=200)
    parser.add_argument('--log_dir', type=str, default='experiments/scopa_dqn_result/')
    parser.add_argument('--load_checkpoint_path', type=str, default='')
    parser.add_argument('--save_every', type=int, default=-1)
    parser.add_argument('--cuda', type=str, default='')
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = args.cuda
    train(args)
