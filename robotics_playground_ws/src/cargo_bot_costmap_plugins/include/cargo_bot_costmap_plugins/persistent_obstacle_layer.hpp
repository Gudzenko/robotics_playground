#ifndef CARGO_BOT_COSTMAP_PLUGINS__PERSISTENT_OBSTACLE_LAYER_HPP_
#define CARGO_BOT_COSTMAP_PLUGINS__PERSISTENT_OBSTACLE_LAYER_HPP_

#include <mutex>
#include <string>

#include "nav2_costmap_2d/layer.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "rclcpp/rclcpp.hpp"

namespace cargo_bot_costmap_plugins
{

class PersistentObstacleLayerTestPeer;

class PersistentObstacleLayer : public nav2_costmap_2d::Layer
{
public:
  void onInitialize() override;
  void updateBounds(
    double robot_x, double robot_y, double robot_yaw,
    double * min_x, double * min_y, double * max_x, double * max_y) override;
  void updateCosts(
    nav2_costmap_2d::Costmap2D & master_grid,
    int min_i, int min_j, int max_i, int max_j) override;
  void reset() override;
  bool isClearable() override;

private:
  friend class PersistentObstacleLayerTestPeer;

  void mapCallback(const nav_msgs::msg::OccupancyGrid::SharedPtr message);

  std::mutex mutex_;
  nav_msgs::msg::OccupancyGrid::SharedPtr map_;
  rclcpp::Subscription<nav_msgs::msg::OccupancyGrid>::SharedPtr subscription_;
};

}  // namespace cargo_bot_costmap_plugins

#endif  // CARGO_BOT_COSTMAP_PLUGINS__PERSISTENT_OBSTACLE_LAYER_HPP_
