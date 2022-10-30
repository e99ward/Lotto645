import tensorflow as tf
keras = tf.keras
import numpy as np

window_size = 24
batch_size = 24

class LottoML:

    def __init__(self):
        self.numbers = []
        self.updated = False
        pass

    def Coordinator(self, mode = False):
        nPred = []
        numadd = np.array(self.numbers).flatten()
        series = np.append(self.series, numadd)
        split_time = len(series) - 96
        # time = np.arange(len(series))
        # time_train = time[:]
        # time_valid = time[split_time:]
        # x_train = series[:]
        x_valid = series[split_time:]
        if mode:
            print("do learning")
            keras.backend.clear_session()
            tf.random.set_seed(42)
            np.random.seed(42)

            train_set = self.window_dataset(series, window_size, batch_size)
            valid_set = self.window_dataset(x_valid, window_size, batch_size)
            model = keras.models.Sequential([
                    keras.layers.Lambda(lambda x: tf.expand_dims(x, axis=-1), input_shape=[None]),
                    keras.layers.SimpleRNN(24, return_sequences=True),
                    keras.layers.SimpleRNN(24),
                    keras.layers.Dense(1),
                    keras.layers.Lambda(lambda x: x * 100.0)
            ])
            optimizer = keras.optimizers.SGD(learning_rate=1.5e-5, momentum=0.9)
            model.compile(loss=keras.losses.Huber(), optimizer=optimizer, metrics=["mae"])
            early_stopping = keras.callbacks.EarlyStopping(patience=20)
            model_checkpoint = keras.callbacks.ModelCheckpoint('./my_checkpoint.h5', save_best_only=True)
            model.fit(train_set, epochs=200,
                    validation_data=valid_set,
                    callbacks=[early_stopping, model_checkpoint])
            model = keras.models.load_model('./my_checkpoint.h5')
            pred_nums = self.get_numbers(model, x_valid)
            nPred = self.formatPredNums(pred_nums)
            print("end prediction")
            print(pred_nums)
        else:
            print("use saved model")
            model = keras.models.load_model('./saved_model.h5')
            pred_nums = self.get_numbers(model, x_valid)
            nPred = self.formatPredNums(pred_nums)
            print("end prediction")
            print(pred_nums)
        return nPred

    def formatPredNums(self, nums):
        numsLotto = []
        for i in range(6):
            val = round(nums[i])
            if val < 1:
                val = 1
            elif val > 45:
                val = 45
            else:
                pass
            numsLotto.append(val)
        return numsLotto

    def LoadNumbersCSV(self):
        nn = np.loadtxt('./numbers.csv', delimiter=',', dtype=np.int32)
        draw = nn[:,0]
        nums = nn[:,1:]
        self.lastdraw = draw[-1]
        print("last saved: ", self.lastdraw)
        print("last saved: ", nums[-1])
        self.series = nums.flatten()
        # print('nums_from_file', self.series)

    def SaveNumbersCSV(self):
        filename = './numbers.csv'
        with open(filename, 'a') as handle:
            draw = self.lastdraw
            for idx in range(len(self.numbers)):
                draw += 1
                handle.write('{}'.format(draw))
                for value in self.numbers[idx]:
                    handle.write(',{}'.format(value))
                handle.write('\n')

    def PassNumbers(self, nums):
        self.numbers.append(nums)
        print("number added: ", self.numbers)

    # main algorism (from Udacity.com)

    def window_dataset(self, series, window_size, batch_size=32, shuffle_buffer=500):
        dataset = tf.data.Dataset.from_tensor_slices(series)
        dataset = dataset.window(window_size + 1, shift=1, drop_remainder=True)
        dataset = dataset.flat_map(lambda window: window.batch(window_size + 1))
        dataset = dataset.shuffle(shuffle_buffer)
        dataset = dataset.map(lambda window: (window[:-1], window[-1]))
        dataset = dataset.batch(batch_size).prefetch(1)
        return dataset

    def model_forecast(self, model, series, window_size, batch_size=24):
        ds = tf.data.Dataset.from_tensor_slices(series)
        ds = ds.window(window_size, shift=1, drop_remainder=True)
        ds = ds.flat_map(lambda w: w.batch(window_size))
        ds = ds.batch(batch_size).prefetch(1)
        forecast = model.predict(ds)
        return forecast

    def get_next_number(self, model, extended_series):
        rnn_forecast_next = self.model_forecast(model, extended_series, window_size)[:, 0]
        return rnn_forecast_next[-1]

    def get_numbers(self, model, series):
        series_new = series
        for i in range(6):
            gnxnum = self.get_next_number(model, series_new)
            series_new = np.append(series_new, gnxnum)
        return series_new[-6:]
