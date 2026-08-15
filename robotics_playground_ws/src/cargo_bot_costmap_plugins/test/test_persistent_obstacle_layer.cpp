#include <gtest/gtest.h>

#include <memory>

#include "cargo_bot_costmap_plugins/persistent_obstacle_layer.hpp"
#include "nav2_costmap_2d/cost_values.hpp"
#include "nav2_costmap_2d/costmap_2d.hpp"

namespace cargo_bot_costmap_plugins
{

class PersistentObstacleLayerTestPeer
{
public:
  static void setMap(
    PersistentObstacleLayer & layer,
    const nav_msgs::msg::OccupancyGrid::SharedPtr & map)
  {
    layer.enabled_ = true;
    layer.map_ = map;
  }
};

nav_msgs::msg::OccupancyGrid::SharedPtr makeMap(bool occupied)
{
  auto map = std::make_shared<nav_msgs::msg::OccupancyGrid>();
  map->info.resolution = 1.0;
  map->info.width = 4;
  map->info.height = 4;
  map->data.assign(16, 0);
  if (occupied) {
    map->data[1 * map->info.width + 2] = 100;
  }
  return map;
}

TEST(PersistentObstacleLayer, MarksAndRemovesMasterCost)
{
  PersistentObstacleLayer layer;
  nav2_costmap_2d::Costmap2D master(4, 4, 1.0, 0.0, 0.0, 0);

  PersistentObstacleLayerTestPeer::setMap(layer, makeMap(true));
  layer.updateCosts(master, 0, 0, 4, 4);
  EXPECT_EQ(master.getCost(2, 1), nav2_costmap_2d::LETHAL_OBSTACLE);

  master.resetMap(0, 0, 4, 4);
  PersistentObstacleLayerTestPeer::setMap(layer, makeMap(false));
  layer.updateCosts(master, 0, 0, 4, 4);
  EXPECT_EQ(master.getCost(2, 1), nav2_costmap_2d::FREE_SPACE);
}

TEST(PersistentObstacleLayer, ResetCannotEraseRememberedObstacle)
{
  PersistentObstacleLayer layer;
  nav2_costmap_2d::Costmap2D master(4, 4, 1.0, 0.0, 0.0, 0);
  PersistentObstacleLayerTestPeer::setMap(layer, makeMap(true));

  layer.reset();
  layer.updateCosts(master, 0, 0, 4, 4);

  EXPECT_FALSE(layer.isClearable());
  EXPECT_EQ(master.getCost(2, 1), nav2_costmap_2d::LETHAL_OBSTACLE);
}

TEST(PersistentObstacleLayer, RespectsUpdateWindowAndMapBounds)
{
  PersistentObstacleLayer layer;
  nav2_costmap_2d::Costmap2D master(2, 2, 1.0, 2.0, 1.0, 0);
  PersistentObstacleLayerTestPeer::setMap(layer, makeMap(true));

  layer.updateCosts(master, 1, 1, 2, 2);
  EXPECT_EQ(master.getCost(0, 0), nav2_costmap_2d::FREE_SPACE);
  EXPECT_EQ(master.getCost(0, 1), nav2_costmap_2d::FREE_SPACE);
}

}  // namespace cargo_bot_costmap_plugins
