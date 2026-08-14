#include "cargo_bot_costmap_plugins/persistent_obstacle_layer.hpp"

#include <algorithm>
#include <functional>
#include <memory>

#include "nav2_costmap_2d/cost_values.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace cargo_bot_costmap_plugins
{

void PersistentObstacleLayer::onInitialize()
{
  auto node = node_.lock();
  if (!node) {
    throw std::runtime_error("PersistentObstacleLayer lifecycle node expired");
  }
  declareParameter("enabled", rclcpp::ParameterValue(true));
  declareParameter("topic", rclcpp::ParameterValue("/persistent_obstacle_map"));
  node->get_parameter(name_ + ".enabled", enabled_);
  std::string topic;
  node->get_parameter(name_ + ".topic", topic);
  rclcpp::SubscriptionOptions options;
  options.callback_group = callback_group_;
  subscription_ = node->create_subscription<nav_msgs::msg::OccupancyGrid>(
    topic, rclcpp::QoS(1).reliable(),
    std::bind(&PersistentObstacleLayer::mapCallback, this, std::placeholders::_1),
    options);
  current_ = true;
}

void PersistentObstacleLayer::mapCallback(
  const nav_msgs::msg::OccupancyGrid::SharedPtr message)
{
  std::lock_guard<std::mutex> lock(mutex_);
  map_ = message;
}

void PersistentObstacleLayer::updateBounds(
  double, double, double, double * min_x, double * min_y,
  double * max_x, double * max_y)
{
  if (!enabled_) {
    return;
  }
  auto * master = layered_costmap_->getCostmap();
  *min_x = std::min(*min_x, master->getOriginX());
  *min_y = std::min(*min_y, master->getOriginY());
  *max_x = std::max(
    *max_x, master->getOriginX() + master->getSizeInMetersX());
  *max_y = std::max(
    *max_y, master->getOriginY() + master->getSizeInMetersY());
}

void PersistentObstacleLayer::updateCosts(
  nav2_costmap_2d::Costmap2D & master_grid,
  int min_i, int min_j, int max_i, int max_j)
{
  if (!enabled_) {
    return;
  }
  nav_msgs::msg::OccupancyGrid::SharedPtr map;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    map = map_;
  }
  if (!map) {
    return;
  }
  const auto & info = map->info;
  for (unsigned int row = 0; row < info.height; ++row) {
    for (unsigned int column = 0; column < info.width; ++column) {
      if (map->data[row * info.width + column] < 100) {
        continue;
      }
      const double world_x =
        info.origin.position.x + (column + 0.5) * info.resolution;
      const double world_y =
        info.origin.position.y + (row + 0.5) * info.resolution;
      unsigned int master_x;
      unsigned int master_y;
      if (!master_grid.worldToMap(world_x, world_y, master_x, master_y)) {
        continue;
      }
      if (
        static_cast<int>(master_x) >= min_i &&
        static_cast<int>(master_x) < max_i &&
        static_cast<int>(master_y) >= min_j &&
        static_cast<int>(master_y) < max_j)
      {
        master_grid.setCost(
          master_x, master_y, nav2_costmap_2d::LETHAL_OBSTACLE);
      }
    }
  }
}

void PersistentObstacleLayer::reset()
{
}

bool PersistentObstacleLayer::isClearable()
{
  return false;
}

}  // namespace cargo_bot_costmap_plugins

PLUGINLIB_EXPORT_CLASS(
  cargo_bot_costmap_plugins::PersistentObstacleLayer,
  nav2_costmap_2d::Layer)
