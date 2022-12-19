# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import cython
from datetime import datetime

import numba

from Core.Crawler import Crawler


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from External.performer.performer.networks.model import Performer

class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, method, supports, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = Performer(num_heads=num_heads, key_dim=embed_dim,
                             attention_method=method, supports=supports)
        self.ffn = keras.Sequential(
            [layers.Dense(ff_dim, activation="relu"), layers.Dense(embed_dim),]
        )
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training):
        attn_output = self.att([inputs, inputs])
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)


def get_model(resolution):
    dim0 = 1
    num_heads = 2  # Number of attention heads
    ff_dim = 32  # Hidden layer size in feed forward network inside transformer
    method = 'linear'
    supports = 10

    inputs = layers.Input(shape=resolution)
    transformer_block = TransformerBlock(dim0, num_heads,
                                         ff_dim, method, supports)
    x = transformer_block(inputs)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(20, activation="relu")(x)
    x = layers.Dropout(0.1)(x)
    outputs = layers.Dense(2, activation="softmax")(x)

    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    #history = model.fit(
    #    x_train, y_train, batch_size=32, epochs=2, validation_data=(x_val, y_val)
    #)
    return model
    
def route_response(crawler:Crawler):
    @cython.cdivision(True)
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cfunc
    async def _route_response(route):
        if(route.request.resource_type in {"media", "font"}):
            #print(f"Blocked resource: {route.request.resource_type}")
            await route.abort()
        else:
            await route.continue_()
    return _route_response

async def full_pipeline():
    sites = {
        "duckduckgo.com": ["https://duckduckgo.com/?t=ffab&q=scraping+test&atb=v320-1&ia=web", ],
    }

    crawler = Crawler(sites, remove_old_data=True, use_resources=False, use_session=False, headless=True)

    crawler.add_pipe("routing", ("**/*", route_response))

    await crawler.open()
    start_time = datetime.now()
    await crawler.crawl(levels=1, max_tabs=50, num_contexts=5)
    print(f"Crawling time: {datetime.now() - start_time}")
    print(f"Got {len(crawler.crawler_visited_urls)} URLs")
    await crawler.close()

if(__name__ == "__main__"):
    asyncio.run(full_pipeline())
