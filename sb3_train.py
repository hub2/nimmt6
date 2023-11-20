from nimmt_gym import NimmtEnv
from stable_baselines3.common.env_checker import check_env
from gymnasium.utils import env_checker
from gymnasium.envs.registration import register
import gymnasium as gym
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3 import PPO, TD3, A2C


env = NimmtEnv()

check_env(env)
env_checker.check_env(env)

register(
    id="nimmt_gym/NimmtEnv-v0",
    entry_point="nimmt_gym:NimmtEnv",
    max_episode_steps=100,
)

# env = gymnasium.make("nimmt_gym/NimmtEnv-v0")


vec_env = make_vec_env("nimmt_gym/NimmtEnv-v0", n_envs=16)
model = PPO("MultiInputPolicy", vec_env, verbose=1)
model.learn(total_timesteps=5000000)
model.save("ppo_nimmt_history")
