const { ServiceDB } = require('../utils/dbTool/schema/service')

/**
 * To signup the new service
 * return has been saved in DB or not
 * @param  { service_name }
 * @returns { Boolean }
 */
const signup = async (service_name) => {
  // 创建一个实例调用save方法，讲数据存入到数据库中
  const service = new ServiceDB({
    name: service_name,
    used_count: 0
  })
  service
    .save()
    .then(() => {
      return true
    })
    .catch((err) => {
      console.log('err' + err)
      return false
    })
}

const getAll = async () => await ServiceDB.find().exec()

const isExists = async (name) => await ServiceDB.exists({ name: name })

const usedService = async (name) => await ServiceDB.updateOne({ name: name }, { $inc: { used_count: 1 } })

module.exports = {
  signup,
  getAll,
  isExists,
  usedService
}
