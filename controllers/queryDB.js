const { getAll } = require('../models/service')

const handleGetServiceCount = async (req, res) => {
  const result = await getAll()
  res.json({
    code: 20000,
    msg: 'All data responsed',
    data: result
  })
}

module.exports = {
  handleGetServiceCount
}
