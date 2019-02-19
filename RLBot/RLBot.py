from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
import math
import time

class RLBot(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.controller = SimpleControllerState() #Initialize controller

        #Constants
        self.DODGETIME = 0.2
        self.DODGEDISTANCE = 500
        self.DISTANCETOBOOST = 1500
        self.POWERSLIDEANGLE = math.radians(170)

        #Game value instance variables
        self.bot_pos = None
        self.bot_rot = None

        #Dodging instance variables
        self.should_dodge = False
        self.on_second_jump = False
        self.next_dodge_time = 0

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.bot_yaw = packet.game_cars[self.team].physics.rotation.yaw
        self.bot_pos = packet.game_cars[self.index].physics.location
        ball_pos = packet.game_ball.physics.location

        self.controller.throttle = 1

        #Check if opponent's goal is behind the ball
        if(self.index == 0 and self.bot_pos.y < ball_pos.y or self.index == 1 and self.bot_pos.y > ball_pos.y):
           self.aim(ball_pos.x, ball_pos.y)

           #Shoot if close enough to ball
           if distance(self.bot_pos.x, self.bot_pos.y, ball_pos.x, ball_pos.y) < DODGEDISTANCE:
               should_dodge = True

        #If not then drive towards own goal (until are behind ball)
        else:
            if self.team == 0:
                self.aim(0, -5000)

            else:
                self.aim(0,5000)

        self.controller.jump = False #makes sure jump only lasts one frame
        self.check_for_dodge()

        #boost when over threshold away
        self.controller.boost = distance(self.bot_pos.x, self.bot_pos.y, ball_pos.x, ball_pos.y) > DISTANCETOBOOST

        if ball_pos.x == 0 and ball_pos.y == 0:
            self.aim(ball_pos.x, ball_pos.y)
            self.controller.boost = True


        return self.controller

    def aim(self, target_x, target_y):
        angle_between_bot_and_target = math.atan2(target_y - self.bot_pos.y,
                                                target_x - self.bot_pos.x)

        angle_front_to_target = angle_between_bot_and_target - self.bot_yaw

        # Correct the values
        if angle_front_to_target < -math.pi:
            angle_front_to_target += 2 * math.pi
        if angle_front_to_target > math.pi:
            angle_front_to_target -= 2 * math.pi

        if angle_front_to_target < math.radians(-10):
            # If the target is more than 10 degrees right from the centre, steer left
            self.controller.steer = -1
        elif angle_front_to_target > math.radians(10):
            # If the target is more than 10 degrees left from the centre, steer right
            self.controller.steer = 1
        else:
            # If the target is less than 10 degrees from the centre, steer straight
            self.controller.steer = 0

        #powerslide if angle greater than threshold
        self.controller.handbrake = abs(math.degrees(angle_front_to_target)) < self.POWERSLIDE_ANGLE

    def check_for_dodge(self):

        if self.should_dodge and time.time() > self.next_dodge_time:

            self.controller.jump = True
            self.controller.pitch = -1 #tilts stick fully forward

            if self.on_second_jump:
                self.on_second_jump = False
                self.should_dodge

            else:
                self.on_second_jump = True
                self.next_dodge_time = time.time() + self.DODGETIME
            
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
