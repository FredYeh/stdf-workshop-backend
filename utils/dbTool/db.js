var mongoose = require('mongoose')

module.exports = () => {
  mongoose.set('useFindAndModify', false)
  mongoose.connect('mongodb://localhost:27017/STDFWorkShop', {
    useUnifiedTopology: true,
    useNewUrlParser: true
  })

  mongoose.connection.on('error', console.error.bind(console, 'connection error:'))
  mongoose.connection.once('open', () => console.log('Database connect success...'))
}
