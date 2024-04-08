import os
import numpy as np
import tensorflow as tf
from tqdm import tqdm
from model import NeuralStyleTransferModel
import settings
import utils

class NeuralStyleTransfer:
    def __init__(self):
        # 初始化模型
        self.model = NeuralStyleTransferModel()
        # 加载内容图片和风格图片
        self.content_image = utils.load_images(settings.CONTENT_IMAGE_PATH)
        self.style_image = utils.load_images(settings.STYLE_IMAGE_PATH)
        # 计算目标内容图片的内容特征和风格图片的风格特征
        self.target_content_features = self.model([self.content_image, ])['content']
        self.target_style_features = self.model([self.style_image, ])['style']
        # 初始化损失计算相关的变量
        self.M = settings.WIDTH * settings.HEIGHT
        self.N = 3
        self.optimizer = tf.keras.optimizers.Adam(settings.LEARNING_RATE)
        # 基于内容图片随机生成一张噪声图片
        self.noise_image = tf.Variable(
            (self.content_image + np.random.uniform(-0.2, 0.2, (1, settings.HEIGHT, settings.WIDTH, 3))) / 2)
        # 创建保存生成图片的文件夹
        self.output_dir = settings.OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _compute_content_loss(self, noise_features, target_features):
        # 计算指定层上两个特征之间的内容loss
        content_loss = tf.reduce_sum(tf.square(noise_features - target_features))
        num_pixels = self.M * self.N
        content_loss = content_loss / (2. * num_pixels)
        return content_loss

    def compute_content_loss(self, noise_content_features):
        # 计算并当前图片的内容loss
        content_losses = []
        for (noise_feature, content_weight), (target_feature, _) in zip(noise_content_features, self.target_content_features):
            layer_content_loss = self._compute_content_loss(noise_feature, target_feature)
            content_losses.append(layer_content_loss * content_weight)
        return tf.add_n(content_losses)

    def gram_matrix(self, feature):
        # 计算给定特征的格拉姆矩阵
        feature = tf.transpose(feature, perm=[1, 2, 0])
        feature = tf.reshape(feature, [tf.shape(feature)[1], -1])
        return tf.matmul(feature, feature, transpose_b=True)

    def _compute_style_loss(self, noise_feature, target_feature):
        # 计算指定层上两个特征之间的风格loss
        noise_gram_matrix = self.gram_matrix(noise_feature)
        style_gram_matrix = self.gram_matrix(target_feature)
        style_loss = tf.reduce_sum(tf.square(noise_gram_matrix - style_gram_matrix))
        num_style_features = 4. * (self.M ** 2) * (self.N ** 2)
        return style_loss / num_style_features

    def compute_style_loss(self, noise_style_features):
        # 计算并返回图片的风格loss
        style_losses = []
        for (noise_feature, style_weight), (target_feature, _) in zip(noise_style_features, self.target_style_features):
            layer_style_loss = self._compute_style_loss(noise_feature, target_feature)
            style_losses.append(layer_style_loss * style_weight)
        return tf.add_n(style_losses)

    def total_loss(self, noise_features):
        # 计算总损失
        content_loss = self.compute_content_loss(noise_features['content'])
        style_loss = self.compute_style_loss(noise_features['style'])
        return content_loss * settings.CONTENT_LOSS_FACTOR + style_loss * settings.STYLE_LOSS_FACTOR

    def train_one_step(self):
        # 一次迭代过程
        with tf.GradientTape() as tape:
            noise_outputs = self.model([self.noise_image, ])
            loss = self.total_loss(noise_outputs)
        grad = tape.gradient(loss, self.noise_image)
        self.optimizer.apply_gradients([(grad, self.noise_image)])
        return loss

    def train(self, epochs, steps_per_epoch):
        # 共训练指定的epochs个epochs
        for epoch in range(1, epochs + 1):
            with tqdm(total=steps_per_epoch, desc=f'Epoch {epoch}/{epochs}') as pbar:
                for step in range(steps_per_epoch):
                    loss = self.train_one_step()
                    pbar.set_postfix({'loss': f'{loss:.4f}'})
                    pbar.update(1)
                    # 每个epoch保存一次图片
                    output_image_path = os.path.join(self.output_dir, f'{epoch}.jpg')
                    utils.save_image(self.noise_image, output_image_path)

