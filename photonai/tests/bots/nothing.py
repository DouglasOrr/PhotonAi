import photonai.bot


class Bot(photonai.bot.SimpleBot):
    def get_control(self, world, ship):
        print('I can use print - it goes to stderr', flush=True)
        return self.Control()


if __name__ == '__main__':
    Bot().run_loop()
