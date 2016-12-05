import photonai.bot


class Bot(photonai.bot.SimpleBot):
    def get_control(self, world, ship):
        print("I'm at %s" % ship.position)
        return self.Control(
            fire=True,
            rotate=-1.0,
            thrust=1.0,
        )


if __name__ == '__main__':
    Bot().run_loop()
